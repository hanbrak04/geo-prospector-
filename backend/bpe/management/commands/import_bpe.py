"""Commande d'import des donnees BPE : python manage.py import_bpe

Transforme le fichier parquet (donnees PLATES : chaque ligne repete ses
domaines, sa ville, son departement) en MODELE RELATIONNEL Django :
tables Domaine1/2/3 en cascade + Commune + Equipement dans PostGIS.

Idempotent : la PK de chaque equipement est l'UUID du fichier source et
bulk_create utilise ignore_conflicts -> on peut relancer sans doublons.
"""
import pandas as pd
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from bpe.models import Commune, Domaine1, Domaine2, Domaine3, Equipement

REGION = "28"  # Normandie - groupe 3
BATCH = 2000   # taille des lots pour bulk_create


class Command(BaseCommand):
    help = "Importe les equipements BPE de la region depuis le fichier parquet"

    def add_arguments(self, parser):
        parser.add_argument("--file", default="/data/bpe25_clean.parquet")
        parser.add_argument("--region", default=REGION)

    def handle(self, *args, **options):
        # ── Etape 1 : EXTRACTION ──
        # filters= est applique PENDANT la lecture du parquet (format colonne) :
        # les lignes des autres regions ne sont meme pas chargees en memoire
        df = pd.read_parquet(
            options["file"], filters=[("region", "=", options["region"])]
        )
        self.stdout.write(f"{len(df)} lignes pour la region {options['region']}")

        # ── Etape 2 : FILTRAGE ──
        # les lignes sans coordonnees sont inaffichables sur une carte -> on les ecarte
        # + nettoyage des champs texte vides (NaN -> "")
        df = df.dropna(subset=["lon", "lat"]).rename(columns={"_id": "uid"})
        df["nom"] = df["nom"].fillna("")
        df["adresse"] = df["adresse"].fillna("")
        df["codepostal"] = df["codepostal"].fillna("")
        df["SIRET"] = df["SIRET"].fillna("")
        self.stdout.write(f"{len(df)} equipements geolocalises")

        # ── Etapes 3 et 4 : RESTRUCTURATION + CHARGEMENT ──
        self._import_domaines(df)
        communes = self._import_communes(df)
        self._import_equipements(df, communes)
        self.stdout.write(self.style.SUCCESS("Import termine"))

    def _import_domaines(self, df):
        """Reconstruit les 3 tables Domaine en cascade a partir des colonnes
        plates du fichier. drop_duplicates() deduplique : les libelles sont
        stockes une seule fois au lieu d'etre repetes sur chaque equipement."""
        d1 = df[["domaine1_code", "domaine1_libelle"]].drop_duplicates()
        Domaine1.objects.bulk_create(
            [Domaine1(code=r.domaine1_code, libelle=r.domaine1_libelle) for r in d1.itertuples()],
            ignore_conflicts=True,   # un domaine deja present n'est pas recree
        )
        d2 = df[["domaine2_code", "domaine2_libelle", "domaine1_code"]].drop_duplicates()
        Domaine2.objects.bulk_create(
            [
                Domaine2(code=r.domaine2_code, libelle=r.domaine2_libelle, parent_id=r.domaine1_code)
                for r in d2.itertuples()
            ],
            ignore_conflicts=True,
        )
        d3 = df[["domaine3_code", "domaine3_libelle", "domaine2_code"]].drop_duplicates()
        Domaine3.objects.bulk_create(
            [
                Domaine3(code=r.domaine3_code, libelle=r.domaine3_libelle, parent_id=r.domaine2_code)
                for r in d3.itertuples()
            ],
            ignore_conflicts=True,
        )
        self.stdout.write(
            f"domaines: {Domaine1.objects.count()} / {Domaine2.objects.count()} / {Domaine3.objects.count()}"
        )

    def _import_communes(self, df):
        """Cree la table Commune (unique par couple nom+dept) et renvoie un
        dictionnaire "nom|dept" -> id pour brancher les equipements ensuite."""
        pairs = df[["ville", "dept"]].drop_duplicates()
        Commune.objects.bulk_create(
            [Commune(nom=r.ville, dept=r.dept) for r in pairs.itertuples()],
            ignore_conflicts=True,
        )
        communes = {f"{c.nom}|{c.dept}": c.id for c in Commune.objects.all()}
        self.stdout.write(f"communes: {len(communes)}")
        return communes

    def _import_equipements(self, df, communes):
        """Insere les equipements par lots de 2000 avec bulk_create.

        bulk_create groupe les INSERT : ~60 requetes au lieu de 120 000+.
        ignore_conflicts + PK=UUID du fichier -> import relancable sans doublons.
        """
        domaines = {d.code: d.code for d in Domaine3.objects.all()}
        objs = []
        total = 0
        for r in df.itertuples():
            objs.append(
                Equipement(
                    id=r.uid,                       # UUID du parquet = PK
                    nom=r.nom[:255],
                    adresse=r.adresse[:255],
                    codepostal=r.codepostal[:5],
                    siret=str(r.SIRET)[:14],
                    commune_id=communes[f"{r.ville}|{r.dept}"],  # jointure vers Commune
                    domaine3_id=domaines[r.domaine3_code],       # jointure vers Domaine3
                    geom=Point(r.lon, r.lat, srid=4326),         # point PostGIS WGS84
                )
            )
            if len(objs) >= BATCH:
                Equipement.objects.bulk_create(objs, ignore_conflicts=True)
                total += len(objs)
                objs = []
                self.stdout.write(f"{total}...", ending="\r")
        # dernier lot (reste < BATCH)
        if objs:
            Equipement.objects.bulk_create(objs, ignore_conflicts=True)
            total += len(objs)
        self.stdout.write(f"equipements importes: {total}")

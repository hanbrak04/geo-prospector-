import pandas as pd
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from bpe.models import Commune, Domaine1, Domaine2, Domaine3, Equipement

REGION = "28"  # Normandie - groupe 3
BATCH = 2000


class Command(BaseCommand):
    help = "Importe les equipements BPE de la region depuis le fichier parquet"

    def add_arguments(self, parser):
        parser.add_argument("--file", default="/data/bpe25_clean.parquet")
        parser.add_argument("--region", default=REGION)

    def handle(self, *args, **options):
        df = pd.read_parquet(
            options["file"], filters=[("region", "=", options["region"])]
        )
        self.stdout.write(f"{len(df)} lignes pour la region {options['region']}")

        # Lignes sans coordonnees : non affichables sur la carte
        df = df.dropna(subset=["lon", "lat"]).rename(columns={"_id": "uid"})
        df["nom"] = df["nom"].fillna("")
        df["adresse"] = df["adresse"].fillna("")
        df["codepostal"] = df["codepostal"].fillna("")
        df["SIRET"] = df["SIRET"].fillna("")
        self.stdout.write(f"{len(df)} equipements geolocalises")

        self._import_domaines(df)
        communes = self._import_communes(df)
        self._import_equipements(df, communes)
        self.stdout.write(self.style.SUCCESS("Import termine"))

    def _import_domaines(self, df):
        d1 = df[["domaine1_code", "domaine1_libelle"]].drop_duplicates()
        Domaine1.objects.bulk_create(
            [Domaine1(code=r.domaine1_code, libelle=r.domaine1_libelle) for r in d1.itertuples()],
            ignore_conflicts=True,
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
        pairs = df[["ville", "dept"]].drop_duplicates()
        Commune.objects.bulk_create(
            [Commune(nom=r.ville, dept=r.dept) for r in pairs.itertuples()],
            ignore_conflicts=True,
        )
        communes = {f"{c.nom}|{c.dept}": c.id for c in Commune.objects.all()}
        self.stdout.write(f"communes: {len(communes)}")
        return communes

    def _import_equipements(self, df, communes):
        domaines = {d.code: d.code for d in Domaine3.objects.all()}
        objs = []
        total = 0
        for r in df.itertuples():
            objs.append(
                Equipement(
                    id=r.uid,
                    nom=r.nom[:255],
                    adresse=r.adresse[:255],
                    codepostal=r.codepostal[:5],
                    siret=str(r.SIRET)[:14],
                    commune_id=communes[f"{r.ville}|{r.dept}"],
                    domaine3_id=domaines[r.domaine3_code],
                    geom=Point(r.lon, r.lat, srid=4326),
                )
            )
            if len(objs) >= BATCH:
                Equipement.objects.bulk_create(objs, ignore_conflicts=True)
                total += len(objs)
                objs = []
                self.stdout.write(f"{total}...", ending="\r")
        if objs:
            Equipement.objects.bulk_create(objs, ignore_conflicts=True)
            total += len(objs)
        self.stdout.write(f"equipements importes: {total}")

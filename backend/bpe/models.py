import uuid

from django.contrib.auth.models import User
from django.contrib.gis.db import models  # models geographiques (PointField, index spatial)


# ── Nomenclature BPE : 3 niveaux en cascade ──────────────────────
# Le fichier source repete ces infos en clair sur chaque ligne ;
# le modele relationnel les sort en tables de reference liees par FK.

class Domaine1(models.Model):
    """Niveau 1 de la nomenclature BPE (ex. A = Services pour les particuliers)."""

    code = models.CharField(max_length=8, primary_key=True)  # code INSEE = PK naturelle
    libelle = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class Domaine2(models.Model):
    """Niveau 2 (ex. A1 = Services publics)."""

    code = models.CharField(max_length=8, primary_key=True)
    libelle = models.CharField(max_length=255)
    parent = models.ForeignKey(Domaine1, related_name="enfants", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class Domaine3(models.Model):
    """Niveau 3, le type d'equipement (ex. A129 = Mairie)."""

    code = models.CharField(max_length=8, primary_key=True)
    libelle = models.CharField(max_length=255)
    parent = models.ForeignKey(Domaine2, related_name="enfants", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class Commune(models.Model):
    """Commune = couple (nom, departement) : deux communes peuvent avoir le
    meme nom dans des departements differents, d'ou la contrainte unique."""

    nom = models.CharField(max_length=255)
    dept = models.CharField(max_length=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom", "dept"], name="uniq_commune_nom_dept")
        ]
        indexes = [models.Index(fields=["nom"])]  # accelere la recherche par nom (?q=)

    def __str__(self):
        return f"{self.nom} ({self.dept})"


class Equipement(models.Model):
    """Equipement du referentiel BPE (lecture seule cote utilisateurs)."""

    # PK = UUID du fichier parquet : permet un import idempotent
    # (relancer import_bpe ne cree pas de doublons)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    codepostal = models.CharField(max_length=5, blank=True)
    siret = models.CharField(max_length=14, blank=True)
    commune = models.ForeignKey(
        Commune, related_name="equipements", on_delete=models.CASCADE
    )
    # PROTECT : on ne peut pas supprimer un type d'equipement encore utilise
    domaine3 = models.ForeignKey(
        Domaine3, related_name="equipements", on_delete=models.PROTECT
    )
    # PointField + spatial_index=True -> index GiST PostGIS :
    # rend la requete "points dans la bbox visible" quasi instantanee
    geom = models.PointField(srid=4326, spatial_index=True)

    class Meta:
        indexes = [models.Index(fields=["domaine3"]), models.Index(fields=["commune"])]

    def __str__(self):
        return self.nom or f"Equipement {self.id}"


class Implantation(models.Model):
    """Implantation commerciale potentielle saisie par un utilisateur.

    Donnee privee : chaque utilisateur ne voit que les siennes
    (filtre sur request.user dans le ViewSet).
    """

    user = models.ForeignKey(
        User, related_name="implantations", on_delete=models.CASCADE
    )
    titre = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True)
    # type de commerce optionnel, dans la meme nomenclature BPE
    domaine3 = models.ForeignKey(
        Domaine3,
        related_name="implantations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    geom = models.PointField(srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre

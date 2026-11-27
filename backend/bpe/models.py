import uuid

from django.contrib.auth.models import User
from django.contrib.gis.db import models


class Domaine1(models.Model):
    """Niveau 1 de la nomenclature BPE (ex. A = Services pour les particuliers)."""

    code = models.CharField(max_length=8, primary_key=True)
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
    nom = models.CharField(max_length=255)
    dept = models.CharField(max_length=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom", "dept"], name="uniq_commune_nom_dept")
        ]
        indexes = [models.Index(fields=["nom"])]

    def __str__(self):
        return f"{self.nom} ({self.dept})"


class Equipement(models.Model):
    """Equipement du referentiel BPE (lecture seule)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    codepostal = models.CharField(max_length=5, blank=True)
    siret = models.CharField(max_length=14, blank=True)
    commune = models.ForeignKey(
        Commune, related_name="equipements", on_delete=models.CASCADE
    )
    domaine3 = models.ForeignKey(
        Domaine3, related_name="equipements", on_delete=models.PROTECT
    )
    geom = models.PointField(srid=4326, spatial_index=True)

    class Meta:
        indexes = [models.Index(fields=["domaine3"]), models.Index(fields=["commune"])]

    def __str__(self):
        return self.nom or f"Equipement {self.id}"


class Implantation(models.Model):
    """Implantation commerciale potentielle saisie par un utilisateur."""

    user = models.ForeignKey(
        User, related_name="implantations", on_delete=models.CASCADE
    )
    titre = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True)
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

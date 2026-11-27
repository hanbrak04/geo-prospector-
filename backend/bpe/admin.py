"""Configuration de l'interface d'administration Django (/admin/).

Permet de gerer les donnees sans ecrire de code : visualiser, rechercher,
modifier equipements, domaines, communes et implantations.
"""
from django.contrib.gis import admin  # admin geographique (carte sur les champs Point)

from .models import Commune, Domaine1, Domaine2, Domaine3, Equipement, Implantation


@admin.register(Domaine1)
class Domaine1Admin(admin.ModelAdmin):
    list_display = ["code", "libelle"]  # colonnes affichees dans la liste


@admin.register(Domaine2)
class Domaine2Admin(admin.ModelAdmin):
    list_display = ["code", "libelle", "parent"]
    list_filter = ["parent"]  # filtre lateral par domaine parent


@admin.register(Domaine3)
class Domaine3Admin(admin.ModelAdmin):
    list_display = ["code", "libelle", "parent"]
    list_filter = ["parent__parent"]  # filtre par domaine de niveau 1 (via la cascade)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ["nom", "dept"]
    search_fields = ["nom"]  # barre de recherche sur le nom


@admin.register(Equipement)
class EquipementAdmin(admin.GISModelAdmin):
    # GISModelAdmin : affiche une carte pour visualiser/editer le champ geom
    list_display = ["nom", "ville", "domaine3"]
    list_filter = ["domaine3__parent__parent"]
    search_fields = ["nom", "siret"]

    @admin.display()
    def ville(self, obj):
        """Colonne calculee : nom de la commune via la FK."""
        return obj.commune.nom


@admin.register(Implantation)
class ImplantationAdmin(admin.GISModelAdmin):
    list_display = ["titre", "user", "created_at"]

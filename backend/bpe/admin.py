from django.contrib.gis import admin

from .models import Commune, Domaine1, Domaine2, Domaine3, Equipement, Implantation


@admin.register(Domaine1)
class Domaine1Admin(admin.ModelAdmin):
    list_display = ["code", "libelle"]


@admin.register(Domaine2)
class Domaine2Admin(admin.ModelAdmin):
    list_display = ["code", "libelle", "parent"]
    list_filter = ["parent"]


@admin.register(Domaine3)
class Domaine3Admin(admin.ModelAdmin):
    list_display = ["code", "libelle", "parent"]
    list_filter = ["parent__parent"]


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ["nom", "dept"]
    search_fields = ["nom"]


@admin.register(Equipement)
class EquipementAdmin(admin.GISModelAdmin):
    list_display = ["nom", "ville", "domaine3"]
    list_filter = ["domaine3__parent__parent"]
    search_fields = ["nom", "siret"]

    @admin.display()
    def ville(self, obj):
        return obj.commune.nom


@admin.register(Implantation)
class ImplantationAdmin(admin.GISModelAdmin):
    list_display = ["titre", "user", "created_at"]

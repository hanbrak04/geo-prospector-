"""Routes de l'API Geo Prospector (toutes prefixees par /api/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Le router DRF genere automatiquement les routes REST du ViewSet :
# GET/POST   /api/implantations/      (liste + creation)
# GET/PUT/DELETE /api/implantations/<id>/  (detail, modification, suppression)
router = DefaultRouter()
router.register("implantations", views.ImplantationViewSet, basename="implantation")

urlpatterns = [
    # "search/" declare AVANT "equipements/" : Django teste les routes dans
    # l'ordre, sinon "search" serait interprete comme un segment de l'autre route
    path("equipements/search/", views.equipement_search),   # GET ?q= : recherche par nom
    path("equipements/", views.equipements),                # GET ?bbox= : points de la zone visible (GeoJSON)
    path("domaines/", views.domaines),                      # GET : arbre des domaines a 3 niveaux
    path("communes/", views.communes),                      # GET ?q= : autocompletion des villes
    path("geocode/", views.geocode),                        # GET ?q=&type= : proxy vers la BAN
    path("auth/register/", views.register),                 # POST : creation de compte (+token)
    path("auth/login/", views.login),                       # POST : connexion (+token)
    path("auth/logout/", views.logout),                     # POST : suppression du token
    path("", include(router.urls)),                         # CRUD implantations
]

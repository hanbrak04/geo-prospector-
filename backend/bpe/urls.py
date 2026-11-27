from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("implantations", views.ImplantationViewSet, basename="implantation")

urlpatterns = [
    path("equipements/search/", views.equipement_search),
    path("equipements/", views.equipements),
    path("domaines/", views.domaines),
    path("communes/", views.communes),
    path("geocode/", views.geocode),
    path("auth/register/", views.register),
    path("auth/login/", views.login),
    path("auth/logout/", views.logout),
    path("", include(router.urls)),
]

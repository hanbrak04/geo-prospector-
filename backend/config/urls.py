"""Routeur principal du projet : toutes les URLs passent par ici."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),            # interface d'administration Django
    path('api/', include('bpe.urls')),          # toute l'API REST -> bpe/urls.py
]

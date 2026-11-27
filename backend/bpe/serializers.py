"""Serializers DRF : conversion objets Python/ORM <-> JSON.

Ils servent dans les deux sens :
- sortant : transformer les modeles en JSON renvoye au front
- entrant : valider les donnees recues avant de creer/modifier en base
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Commune, Domaine1, Domaine2, Domaine3, Implantation


# ── Domaines : serializers imbriques pour l'arbre a 3 niveaux ────
# Domaine1Serializer -> contient des Domaine2Serializer -> des Domaine3Serializer
# "enfants" est le related_name de la FK parent dans models.py

class Domaine3Serializer(serializers.ModelSerializer):
    class Meta:
        model = Domaine3
        fields = ["code", "libelle"]


class Domaine2Serializer(serializers.ModelSerializer):
    enfants = Domaine3Serializer(many=True)

    class Meta:
        model = Domaine2
        fields = ["code", "libelle", "enfants"]


class Domaine1Serializer(serializers.ModelSerializer):
    enfants = Domaine2Serializer(many=True)

    class Meta:
        model = Domaine1
        fields = ["code", "libelle", "enfants"]


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = ["id", "nom", "dept"]


class ImplantationSerializer(serializers.ModelSerializer):
    """Le front envoie/recoit des coordonnees simples (lon/lat),
    la base stocke un PointField PostGIS : le serializer fait la traduction."""

    # en entree uniquement (write_only) : le front envoie lon/lat plats
    lon = serializers.FloatField(write_only=True)
    lat = serializers.FloatField(write_only=True)
    # en sortie : geometrie au format GeoJSON pour Leaflet
    geometry = serializers.SerializerMethodField()

    class Meta:
        model = Implantation
        fields = [
            "id",
            "titre",
            "commentaire",
            "domaine3",
            "lon",
            "lat",
            "geometry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_geometry(self, obj):
        """PointField PostGIS -> GeoJSON {type: Point, coordinates: [lon, lat]}."""
        return {
            "type": "Point",
            "coordinates": [obj.geom.x, obj.geom.y],
        }

    def create(self, validated_data):
        """lon/lat recus -> objet Point GEOS stocke dans geom."""
        from django.contrib.gis.geos import Point

        lon = validated_data.pop("lon")
        lat = validated_data.pop("lat")
        validated_data["geom"] = Point(lon, lat, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """lon/lat optionnels a la modification (la position peut ne pas changer)."""
        lon = validated_data.pop("lon", None)
        lat = validated_data.pop("lat", None)
        if lon is not None and lat is not None:
            from django.contrib.gis.geos import Point

            instance.geom = Point(lon, lat, srid=4326)
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription : le mot de passe n'est jamais renvoye (write_only)
    et min_length impose une longueur minimale."""

    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ["username", "password", "email"]

    def create(self, validated_data):
        # create_user (et pas create) : hashe le mot de passe (PBKDF2)
        return User.objects.create_user(**validated_data)

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Commune, Domaine1, Domaine2, Domaine3, Implantation


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
    lon = serializers.FloatField(write_only=True)
    lat = serializers.FloatField(write_only=True)
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
        return {
            "type": "Point",
            "coordinates": [obj.geom.x, obj.geom.y],
        }

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lon = validated_data.pop("lon")
        lat = validated_data.pop("lat")
        validated_data["geom"] = Point(lon, lat, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lon = validated_data.pop("lon", None)
        lat = validated_data.pop("lat", None)
        if lon is not None and lat is not None:
            from django.contrib.gis.geos import Point

            instance.geom = Point(lon, lat, srid=4326)
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ["username", "password", "email"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

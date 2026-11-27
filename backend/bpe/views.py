import json
from urllib.parse import urlencode
from urllib.request import urlopen

from django.contrib.auth import authenticate
from django.contrib.gis.geos import Polygon
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Commune, Domaine1, Equipement, Implantation
from .serializers import (
    CommuneSerializer,
    Domaine1Serializer,
    ImplantationSerializer,
    RegisterSerializer,
)

EQUIPEMENT_LIMIT = 5000


def _parse_bbox(request):
    raw = request.query_params.get("bbox")
    if not raw:
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in raw.split(","))
    except ValueError:
        return None
    return Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))


@api_view(["GET"])
@permission_classes([AllowAny])
def equipements(request):
    """Equipements dans la bbox affichee, filtres par domaines et communes.

    Retourne du GeoJSON pour affichage direct dans Leaflet.
    """
    bbox = _parse_bbox(request)
    if bbox is None:
        return Response(
            {"detail": "parametre bbox=minLon,minLat,maxLon,maxLat requis"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = Equipement.objects.filter(geom__bboverlaps=bbox).select_related(
        "commune", "domaine3"
    )

    for param, field in (
        ("d1", "domaine3__parent__parent__code__in"),
        ("d2", "domaine3__parent__code__in"),
        ("d3", "domaine3__code__in"),
    ):
        values = request.query_params.get(param)
        if values:
            qs = qs.filter(**{field: values.split(",")})

    communes = request.query_params.get("communes")
    if communes:
        qs = qs.filter(commune_id__in=communes.split(","))

    count = qs.count()
    qs = qs[:EQUIPEMENT_LIMIT]

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [e.geom.x, e.geom.y],
            },
            "properties": {
                "id": str(e.id),
                "nom": e.nom,
                "adresse": e.adresse,
                "codepostal": e.codepostal,
                "ville": e.commune.nom,
                "dept": e.commune.dept,
                "siret": e.siret,
                "domaine3_code": e.domaine3.code,
                "domaine3_libelle": e.domaine3.libelle,
            },
        }
        for e in qs
    ]

    return Response(
        {
            "type": "FeatureCollection",
            "count": count,
            "truncated": count > EQUIPEMENT_LIMIT,
            "features": features,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def equipement_search(request):
    """Recherche d'equipements par nom (?q=) sur toute la region."""
    q = request.query_params.get("q", "").strip()
    if len(q) < 2:
        return Response([])

    qs = Equipement.objects.filter(nom__icontains=q).select_related(
        "commune", "domaine3"
    )[:20]

    return Response(
        [
            {
                "id": str(e.id),
                "nom": e.nom,
                "adresse": e.adresse,
                "codepostal": e.codepostal,
                "ville": e.commune.nom,
                "siret": e.siret,
                "domaine3_libelle": e.domaine3.libelle,
                "lon": e.geom.x,
                "lat": e.geom.y,
            }
            for e in qs
        ]
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def domaines(request):
    """Arbre complet des domaines (3 niveaux) pour les filtres."""
    qs = Domaine1.objects.prefetch_related("enfants__enfants").order_by("code")
    return Response(Domaine1Serializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def geocode(request):
    """Geocode une adresse via api-adresse.data.gouv.fr (BAN).

    GET /api/geocode/?q=12 rue de la republique rouen
    """
    q = request.query_params.get("q", "").strip()
    if len(q) < 3:
        return Response([])

    params = {
        "q": q,
        "limit": 5,
        # centre la recherche sur la Normandie
        "lat": 49.1,
        "lon": 0.4,
    }
    # filtre optionnel : municipality, street, housenumber, locality
    if t := request.query_params.get("type"):
        params["type"] = t

    url = "https://api-adresse.data.gouv.fr/search/?" + urlencode(params)
    try:
        with urlopen(url, timeout=5) as r:
            data = json.load(r)
    except Exception:
        return Response(
            {"detail": "service de geocodage indisponible"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response(
        [
            {
                "label": f["properties"]["label"],
                "city": f["properties"].get("city", ""),
                "lon": f["geometry"]["coordinates"][0],
                "lat": f["geometry"]["coordinates"][1],
            }
            for f in data.get("features", [])
        ]
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def communes(request):
    """Liste des communes (filtre optionnel ?q= sur le nom)."""
    qs = Commune.objects.order_by("nom")
    q = request.query_params.get("q")
    if q:
        qs = qs.filter(nom__icontains=q)
    return Response(CommuneSerializer(qs[:100], many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "username": user.username},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password"),
    )
    if user is None:
        return Response(
            {"detail": "identifiants invalides"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
def logout(request):
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class ImplantationViewSet(viewsets.ModelViewSet):
    """CRUD des implantations potentielles — chaque user ne voit que les siennes."""

    serializer_class = ImplantationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Implantation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

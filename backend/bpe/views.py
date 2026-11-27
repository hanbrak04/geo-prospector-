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

# Nombre max d'equipements renvoyes par requete :
# protege le navigateur (120 764 marqueurs le figeraient).
# Le flag "truncated" previent le front que la reponse est tronquee.
EQUIPEMENT_LIMIT = 5000


def _parse_bbox(request):
    """Parse le parametre ?bbox=minLon,minLat,maxLon,maxLat en polygone PostGIS."""
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

    GET /api/equipements/?bbox=W,S,E,N&d1=A&d2=A1&d3=A129&communes=1,2

    Le front envoie la zone visible a chaque deplacement de la carte :
    on ne charge jamais toute la region, seulement ce qui est affiche.
    Retourne du GeoJSON pour affichage direct dans Leaflet.
    """
    bbox = _parse_bbox(request)
    if bbox is None:
        return Response(
            {"detail": "parametre bbox=minLon,minLat,maxLon,maxLat requis"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # geom__bboverlaps -> operateur && PostGIS : intersection rapide
    # grace a l'index spatial GiST sur Equipement.geom
    # select_related : jointures commune + domaine3 en une seule requete
    # (evite 5000 requetes SQL supplementaires lors de la serialisation)
    qs = Equipement.objects.filter(geom__bboverlaps=bbox).select_related(
        "commune", "domaine3"
    )

    # filtres par domaine : le parametre du niveau choisi filtre via la cascade
    # ex. d1=A -> domaine3->parent (d2) ->parent (d1) -> code = "A"
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

    count = qs.count()          # total reel dans la zone (avant troncature)
    qs = qs[:EQUIPEMENT_LIMIT]  # LIMIT en SQL, pas en Python

    # Serialisation manuelle en GeoJSON FeatureCollection
    # (format compris nativement par le composant <GeoJSON> de react-leaflet)
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
    """Recherche d'equipements par nom (?q=) sur toute la region.

    Contrairement a /equipements/, pas de bbox : la recherche porte
    sur toute la Normandie. icontains = LIKE %q% insensible a la casse.
    """
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
    """Arbre complet des domaines (3 niveaux imbriques) pour les filtres.

    prefetch_related("enfants__enfants") charge les 3 niveaux en 3 requetes
    au lieu d'une par domaine (evite le probleme N+1).
    """
    qs = Domaine1.objects.prefetch_related("enfants__enfants").order_by("code")
    return Response(Domaine1Serializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def geocode(request):
    """Geocode une adresse via api-adresse.data.gouv.fr (BAN).

    GET /api/geocode/?q=12 rue de la republique rouen&type=housenumber

    Le backend fait proxy : le front n'appelle jamais l'API externe
    directement (un seul point d'entree, plus simple a documenter).
    """
    q = request.query_params.get("q", "").strip()
    if len(q) < 3:
        return Response([])

    params = {
        "q": q,
        "limit": 5,
        # biaise la recherche vers le centre de la Normandie
        # (les adresses normandes remontent en premier)
        "lat": 49.1,
        "lon": 0.4,
    }
    # filtre optionnel BAN : municipality, street, housenumber, locality
    # (utilise avec "municipality" pour centrer la carte sur la mairie d'une ville)
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

    # on ne garde que ce dont le front a besoin
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
    """Liste des communes (filtre optionnel ?q= sur le nom, pour l'autocompletion)."""
    qs = Commune.objects.order_by("nom")
    q = request.query_params.get("q")
    if q:
        qs = qs.filter(nom__icontains=q)
    return Response(CommuneSerializer(qs[:100], many=True).data)


# ── Authentification par token ────────────────────────────────────
# Le front stocke le token dans localStorage et le renvoie
# dans le header "Authorization: Token xxx" a chaque requete.

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Creation de compte : le mot de passe est hashe par create_user
    (jamais stocke en clair). Renvoie directement un token = auto-login."""
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
    """Connexion : authenticate() verifie le hash du mot de passe."""
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
    """Deconnexion : suppression du token (requiert d'etre authentifie)."""
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class ImplantationViewSet(viewsets.ModelViewSet):
    """CRUD complet des implantations (GET/POST/PUT/DELETE generes par
    le ModelViewSet + router DRF).

    Securite : IsAuthenticated obligatoire, et chaque utilisateur
    ne voit/modifie que SES implantations (filtre sur request.user).
    """

    serializer_class = ImplantationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Implantation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # le user est injecte depuis le token, jamais depuis le body
        serializer.save(user=self.request.user)

# Geo Prospector — Normandie (Groupe 3)

Plateforme web d'exploration et de prospection commerciale géographique à partir des données
de la **Base permanente des équipements (BPE) de l'INSEE, millésime 2025**, filtrée sur la
région **Normandie (code 28)**.

## Fonctionnalités

- Carte Leaflet publique : affichage des équipements géolocalisés chargés **uniquement pour
  la zone visible** (requête bounding-box à chaque déplacement/zoom).
- Filtres par **domaine sur 3 niveaux** (nomenclature BPE) et par **ville(s)**.
- Popup d'information sur chaque équipement (nom, adresse, type, SIRET).
- **Implantations potentielles** : un utilisateur authentifié ajoute des points avec titre,
  type de commerce (nomenclature BPE) et commentaires — visibles par lui seul (CRUD complet).

## Stack

| Composant  | Technologie                                        |
| ---------- | --------------------------------------------------- |
| Frontend   | React + react-leaflet (Vite)                        |
| Backend    | Python / Django / GeoDjango / Django REST Framework |
| Base       | PostgreSQL + PostGIS                                |
| Conteneurs | docker compose : `db`, `backend`, `frontend`        |

## Installation

```bash
docker compose up --build
```

Puis, dans un autre terminal, appliquer les migrations :

```bash
docker compose exec backend python manage.py migrate
```

## Importation des données

1. Télécharger le fichier parquet nettoyé :
   `https://data.atontour.info/bpe25.parquet.zip` → extraire `bpe25_clean.parquet`
   dans `./data/` (monté sur `/data` dans le conteneur backend).
2. Lancer l'import (filtre `region = 28`, ignore les lignes sans coordonnées) :

```bash
docker compose exec backend python manage.py import_bpe
```

Résultat attendu : ~120 764 équipements, 7 domaines niv. 1, 27 niv. 2, 233 niv. 3,
2 643 communes.

## Utilisation

- Frontend : http://localhost:5173
- API : http://localhost:8000/api/
- Admin Django : http://localhost:8000/admin/ (`docker compose exec backend python manage.py createsuperuser`)

## Modèle de données

```
Domaine1 (code, libelle)                      ex. A — Services pour les particuliers
  └─ Domaine2 (code, libelle, parent→D1)      ex. A1 — Services publics
       └─ Domaine3 (code, libelle, parent→D2) ex. A129 — Mairie

Commune (nom, dept) — unique (nom, dept)

Equipement (id UUID, nom, adresse, codepostal, siret,
            commune→Commune, domaine3→Domaine3, geom Point 4326)

Implantation (user→auth_user, titre, commentaire,
              domaine3→Domaine3 null, geom Point 4326, created_at, updated_at)
```

Le fichier parquet étant plat (colonnes `domaine1_*`, `domaine2_*`, `domaine3_*`,
`ville`, `dept`), l'import reconstruit la hiérarchie des domaines et la table des communes.

## API

| Méthode | Endpoint                     | Auth | Description |
| ------- | ---------------------------- | ---- | ----------- |
| GET     | `/api/equipements/`          | non  | GeoJSON des équipements. **Requis** `bbox=minLon,minLat,maxLon,maxLat`. Filtres : `d1`, `d2`, `d3` (codes séparés par `,`), `communes` (ids séparés par `,`). Limité à 5000 points (`truncated: true` sinon). |
| GET     | `/api/equipements/search/?q=` | non | Recherche d'équipements par nom (`icontains`, max 20 résultats, toute la région). |
| GET     | `/api/domaines/`             | non  | Arbre des domaines (3 niveaux imbriqués). |
| GET     | `/api/communes/?q=`          | non  | Communes (recherche optionnelle sur le nom). |
| GET     | `/api/geocode/?q=`           | non  | Géocodage d'une adresse postale (proxy api-adresse.data.gouv.fr / BAN) → `{label, city, lon, lat}`. |
| POST    | `/api/auth/register/`        | non  | Création de compte `{username, password}` → `{token}`. |
| POST    | `/api/auth/login/`           | non  | Connexion → `{token}` (en-tête `Authorization: Token …`). |
| POST    | `/api/auth/logout/`          | oui  | Supprime le token. |
| GET/POST    | `/api/implantations/`    | oui  | Liste / création des points **de l'utilisateur connecté**. |
| GET/PUT/DELETE | `/api/implantations/<id>/` | oui  | Détail / modification / suppression (propriétaire seul). |

Exemple :

```bash
curl "http://localhost:8000/api/equipements/?bbox=0.9,49.3,1.3,49.6&d1=B&communes=2441"
```

## Post mortem

- Le parquet fourni est déjà nettoyé (colonnes renommées, 3 niveaux de domaine explicites,
  coordonnées WGS84) : le travail relationnel porte surtout sur la reconstruction des
  tables de référence (`Domaine1/2/3`, `Commune`).
- ~4 500 lignes de la région n'ont pas de coordonnées : elles sont ignorées à l'import
  puisque non affichables.
- Le chargement à la volée par bounding-box (`geom__bboverlaps`, index spatial GiST)
  évite de transférer les 120 000 points ; une limite de 5 000 points par requête
  invite à zoomer.
- Écueil macOS rencontré : les fichiers du dossier `frontend` étaient « dataless »
  (iCloud Drive, Desktop & Documents) → erreurs I/O dans le conteneur ; résolu par
  `brctl download` + passage à Vite 7.

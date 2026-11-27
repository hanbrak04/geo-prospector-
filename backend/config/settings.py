"""
Reglages Django du projet Geo Prospector.

Documentation : https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path
import os

# Racine du projet backend (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Securite / dev ---
# Cle secrete de dev uniquement : en production elle sortirait d'une variable d'env
SECRET_KEY = 'django-insecure-+c4$qst9706lo!h_y+-j0o6b(ayyv!g21bqi&640gpq$x@7f0='

DEBUG = True  # mode dev : pages d'erreur detaillees. A mettre a False en production

# hotes autorises : "backend" est le Host envoye par le proxy Vite (vite.config.js),
# sans lui Django rejette les requetes relayees par le frontend
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend"]


# --- Applications ---

INSTALLED_APPS = [
    # apps Django standard (admin, auth, sessions...)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.gis",            # GeoDjango : champs geographiques (PointField)
    "rest_framework",                # Django REST Framework : l'API
    "rest_framework.authtoken",      # authentification par token (Authorization: Token xxx)
    "corsheaders",                   # gestion du CORS (requetes cross-origin)
    "bpe",                           # notre app metier
]

# Toutes les vues DRF attendent un token sauf celles marquees AllowAny
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "corsheaders.middleware.CorsMiddleware",   # ajoute les headers CORS aux reponses
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'   # routeur principal : config/urls.py

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Base de donnees ---

# Moteur PostGIS : obligatoire pour les champs geographiques et l'index spatial.
# Les identifiants viennent des variables d'environnement definies dans docker-compose
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),   # "db" = service docker-compose
        "PORT": os.environ.get("DB_PORT"),
    }
}


# --- Validation des mots de passe (pour register) ---

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- Internationalisation ---

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- Fichiers statiques ---

STATIC_URL = 'static/'


# --- Email (backend console : les mails s'affichent dans les logs, rien n'est envoye) ---

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# --- CORS ---
# En dev, tout passe par le proxy Vite (meme origine) donc le CORS n'est plus
# necessaire ; on le garde pour un acces direct a l'API depuis localhost:5173

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

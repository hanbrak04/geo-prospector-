# Image Python construite pour le backend Django
FROM python:3.12-slim

WORKDIR /app

# Librairies systeme exigees par GeoDjango (PointField, requetes spatiales)
# binutils + gdal + geos : sans elles, Django ne peut pas manipuler les geometries
RUN apt-get update && apt-get install -y \
    binutils \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# pip avant le code : les dependances restent en cache Docker
# si seul le code source change entre deux builds
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

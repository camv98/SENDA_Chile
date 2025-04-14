#!/bin/bash

# Variables
PROJECT_ID="senda-456813"
REGION="southamerica-west1"
REPO_NAME="senda-repo"
IMAGE_NAME="senda_app"
TAG="latest"
FULL_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG"

echo "👉 Habilitando Artifact Registry..."
gcloud services enable artifactregistry.googleapis.com

echo "👉 Creando repositorio (si no existe)..."
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Repo de imágenes de SENDA" 2>/dev/null || echo "Repositorio ya existe"

echo "👉 Autenticando Docker con Artifact Registry..."
gcloud auth configure-docker $REGION-docker.pkg.dev

echo "👉 Construyendo imagen Docker..."
docker build -t $IMAGE_NAME .

echo "👉 Etiquetando imagen..."
docker tag $IMAGE_NAME $FULL_IMAGE

echo "👉 Subiendo imagen a Artifact Registry..."
docker push $FULL_IMAGE

echo "✅ Imagen subida exitosamente: $FULL_IMAGE"


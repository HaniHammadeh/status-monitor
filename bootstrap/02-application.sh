#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")/env.sh"

GREEN="\033[0;32m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m"

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

ok() {
    echo -e "${GREEN}[ OK ]${NC} $1"
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    exit 1
}

###########################################
# Verify Docker
###########################################

command -v docker >/dev/null || fail "Docker not installed"

command -v kubectl >/dev/null || fail "kubectl not installed"

###########################################
# Build image
###########################################

info "Building Docker image..."

docker build \
    --build-arg VERSION="$INITIAL_TAG" \
    --build-arg COMMIT="bootstrap" \
    -t "${DOCKER_IMAGE}:${INITIAL_TAG}" .

ok "Docker image built"

###########################################
# Push image
###########################################

info "Pushing image..."

docker push "${DOCKER_IMAGE}:${INITIAL_TAG}"

ok "Image pushed"

###########################################
# Deploy application
###########################################
info "Deploying PostgreSQL..."
kubectl apply -f k8s/base/postgres/

#kubectl rollout status deployment/postgres -n dev

info "Deploying Redis..."
kubectl apply -f k8s/base/redis/

kubectl rollout status deployment/redis -n dev

info "Deploying ConfigMap..."
#kubectl apply -f k8s/base/config/

info "Deploying API..."
kubectl apply -f k8s/base/api/

kubectl rollout status deployment/api -n dev

info "Deploying Worker..."
kubectl apply -f k8s/base/worker/

info "Deploying Beat..."
kubectl apply -f k8s/base/beat/

# Wait
###########################################

#kubectl rollout status deployment/${APP_NAME} \
#    -n ${DEV_NAMESPACE} \
#    --timeout=180s

ok "Deployment successful"

###########################################
# Health Check
###########################################

SERVICE_IP=$(kubectl get svc ${APP_NAME}-api \
    -n ${DEV_NAMESPACE} \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo
echo "Application deployed."
echo
echo "URL:"
echo
echo "http://${SERVICE_IP}"
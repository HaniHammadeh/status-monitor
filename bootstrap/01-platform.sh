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

info "Checking kubectl..."

command -v kubectl >/dev/null || fail "kubectl not installed"

kubectl cluster-info >/dev/null || fail "Cannot connect to Kubernetes"

ok "Connected to cluster"

apply_directory() {

    local DIR="$1"

    if [ ! -d "$DIR" ]; then
        return
    fi

    info "Applying $(basename "$DIR")"

    kubectl apply -f "$DIR"

    ok "$(basename "$DIR") done"
}

apply_directory "$PLATFORM_DIR/namespaces"
apply_directory "$PLATFORM_DIR/rbac"
apply_directory "$PLATFORM_DIR/secrets"
apply_directory "$PLATFORM_DIR/configmaps"
apply_directory "$PLATFORM_DIR/storage"
apply_directory "$PLATFORM_DIR/certificates"
apply_directory "$PLATFORM_DIR/gateway"
apply_directory "$PLATFORM_DIR/dns"
apply_directory "$PLATFORM_DIR/registry"

info "Verifying namespaces..."

kubectl get namespace "$DEV_NAMESPACE" >/dev/null
kubectl get namespace "$STAGING_NAMESPACE" >/dev/null
kubectl get namespace "$PROD_NAMESPACE" >/dev/null

ok "Platform bootstrap completed successfully"
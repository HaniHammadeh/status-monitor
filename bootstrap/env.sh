#!/usr/bin/env bash

############################################
# Project
############################################

export APP_NAME="status-monitor"

############################################
# Docker
############################################

export DOCKER_IMAGE="hanihammadeh/status-monitor"
export INITIAL_TAG="initial"

############################################
# Namespaces
############################################

export DEV_NAMESPACE="dev"
export STAGING_NAMESPACE="staging"
export PROD_NAMESPACE="prod"

############################################
# Paths
############################################

export PLATFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../platform" && pwd)"
export DEV_MANIFESTS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../k8s/dev" && pwd)"
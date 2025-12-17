#!/usr/bin/env bash
# Generate Mender artifact with bundled Docker images for retina-node
set -euo pipefail

# Usage info
usage() {
  cat <<EOF
Usage: $0 <version> [previous_version]

Generate a Mender artifact for the retina-node stack with bundled Docker images.
Uses the docker-compose.yml file as-is (no version templating).

Arguments:
  version           Artifact version (e.g., v1.2.3, dev) - REQUIRED
  previous_version  Previous version for delta updates - OPTIONAL

Environment variables:
  DEVICE_TYPE       Target device type (default: pi5-v3-arm64)
  PLATFORM          Target platform (default: linux/arm64/v8)
  ARTIFACT_NAME     Artifact name (default: retina-node)
  COMPOSE_FILE      Path to docker-compose file (default: docker-compose.yml)

Examples:
  $0 v1.0.0
  $0 v1.0.1 v1.0.0  # with delta
EOF
  exit 1
}

# Parse arguments
VERSION=${1:-""}
PREV_VERSION=${2:-""}

if [ -z "$VERSION" ]; then
  usage
fi

# Configuration
DEVICE_TYPE=${DEVICE_TYPE:-pi5-v3-arm64}
PLATFORM=${PLATFORM:-linux/arm64/v8}
ARTIFACT_NAME=${ARTIFACT_NAME:-retina-node}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

MANIFEST_DIR="manifests/${VERSION}"
ARTIFACT_OUT="artifacts/${ARTIFACT_NAME}-${VERSION}.mender"
METADATA_OUT="artifacts/${ARTIFACT_NAME}-${VERSION}.json"

# Check prerequisites
command -v app-gen &>/dev/null || { echo "Error: app-gen not found"; exit 1; }
command -v mender-artifact &>/dev/null || { echo "Error: mender-artifact not found"; exit 1; }
command -v docker &>/dev/null || { echo "Error: docker not found"; exit 1; }
[ -f "$COMPOSE_FILE" ] || { echo "Error: Compose file not found: $COMPOSE_FILE"; exit 1; }

echo "Building retina-node artifact ${VERSION}"
[ -n "$PREV_VERSION" ] && echo "  Delta from ${PREV_VERSION}"

# Create output directories
mkdir -p "${MANIFEST_DIR}" artifacts

# Copy compose file to manifest directory (no templating)
cp "${COMPOSE_FILE}" "${MANIFEST_DIR}/docker-compose.yaml"

# Validate compose
docker compose -f "${MANIFEST_DIR}/docker-compose.yaml" config >/dev/null 2>&1 || {
  echo "Error: Invalid docker-compose.yaml"
  exit 1
}

# Extract image tags from docker-compose.yml
echo "Extracting images from docker-compose.yaml..."
IMAGES=$(docker compose -f "${MANIFEST_DIR}/docker-compose.yaml" config --images 2>/dev/null)

if [ -z "$IMAGES" ]; then
  echo "Error: No images found in docker-compose.yaml"
  exit 1
fi

echo "Found images:"
echo "$IMAGES" | sed 's/^/  - /'

# Build app-gen arguments
APP_GEN_ARGS=(
  --artifact-name "${ARTIFACT_NAME}-${VERSION}"
  --device-type "${DEVICE_TYPE}"
  --platform "${PLATFORM}"
  --application-name "${ARTIFACT_NAME}"
  --orchestrator docker-compose
  --manifests-dir "${MANIFEST_DIR}"
  --output-path "${ARTIFACT_OUT}"
)

SOFTWARE_ARGS=(
  --software-name "${ARTIFACT_NAME}"
  --software-version "${VERSION}"
)

# Add images to app-gen arguments
# For delta updates, we'd need previous image tags - keeping it simple for now (full updates only)
if [ -n "$PREV_VERSION" ]; then
  echo "Warning: Delta updates require manual configuration - performing full update"
fi

while IFS= read -r image; do
  [ -n "$image" ] && APP_GEN_ARGS+=(--image "$image")
done <<< "$IMAGES"

# Run app-gen
app-gen "${APP_GEN_ARGS[@]}" -- "${SOFTWARE_ARGS[@]}"

# Validate artifact
mender-artifact validate "${ARTIFACT_OUT}" || {
  echo "Error: Artifact validation failed"
  exit 1
}

# Check size
SIZE=$(stat -c%s "${ARTIFACT_OUT}" 2>/dev/null || stat -f%z "${ARTIFACT_OUT}")
SIZE_MB=$((SIZE / 1024 / 1024))

[ "$SIZE" -gt 2147483648 ] && echo "Warning: Large artifact (${SIZE_MB}MB)"

# Build images JSON object for metadata
IMAGES_JSON=""
FIRST=true
while IFS= read -r image; do
  if [ -n "$image" ]; then
    # Extract image name (last part before :tag)
    NAME=$(echo "$image" | sed 's|.*/||' | sed 's|:.*||')
    if [ "$FIRST" = true ]; then
      IMAGES_JSON="\"${NAME}\": \"${image}\""
      FIRST=false
    else
      IMAGES_JSON="${IMAGES_JSON},\n    \"${NAME}\": \"${image}\""
    fi
  fi
done <<< "$IMAGES"

# Create metadata
cat > "${METADATA_OUT}" <<EOF
{
  "stack_version": "${VERSION}",
  "artifact_name": "${ARTIFACT_NAME}-${VERSION}",
  "previous_version": "${PREV_VERSION:-null}",
  "device_type": "${DEVICE_TYPE}",
  "platform": "${PLATFORM}",
  "artifact_size_bytes": ${SIZE},
  "artifact_size_mb": ${SIZE_MB},
  "delta_enabled": false,
  "images": {
    $(echo -e "$IMAGES_JSON")
  },
  "built_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_sha": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
}
EOF

echo "Done: ${ARTIFACT_OUT} (${SIZE_MB}MB)"

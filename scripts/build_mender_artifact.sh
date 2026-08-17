#!/usr/bin/env bash
# Generate Mender docker-compose artifact for retina-node
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 <version>

Generate a Mender docker-compose artifact for the retina-node stack.
Images are downloaded automatically from registries via skopeo.

Arguments:
  version       Artifact version (e.g., v1.2.3) - REQUIRED

Environment variables:
  DEVICE_TYPE   Target device type (default: pi5-v3-arm64)
  ARTIFACT_NAME Artifact name (default: retina-node)
  COMPOSE_FILE  Path to docker-compose file (default: docker-compose.yml)

Prerequisites:
  mender-artifact    https://docs.mender.io/downloads/workstation-tools
  skopeo             https://github.com/containers/skopeo
  gen_docker-compose curl -O https://raw.githubusercontent.com/mendersoftware/mender-container-modules/1.0.0/src/gen_docker-compose

Examples:
  $0 v1.0.0
EOF
  exit 1
}

VERSION=${1:-""}
if [ -z "$VERSION" ]; then
  usage
fi

DEVICE_TYPE=${DEVICE_TYPE:-pi5-v3-arm64}
ARTIFACT_NAME=${ARTIFACT_NAME:-retina-node}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

MANIFEST_DIR="manifests/${VERSION}"
ARTIFACT_OUT="artifacts/${ARTIFACT_NAME}-${VERSION}.mender"
METADATA_OUT="artifacts/${ARTIFACT_NAME}-${VERSION}.json"

# Check prerequisites
command -v gen_docker-compose &>/dev/null || { echo "Error: gen_docker-compose not found. See usage for install instructions."; exit 1; }
command -v mender-artifact &>/dev/null    || { echo "Error: mender-artifact not found."; exit 1; }
command -v skopeo &>/dev/null             || { echo "Error: skopeo not found."; exit 1; }
[ -f "$COMPOSE_FILE" ]                    || { echo "Error: Compose file not found: $COMPOSE_FILE"; exit 1; }

echo "Building retina-node artifact ${VERSION}"

mkdir -p "${MANIFEST_DIR}" artifacts

# Resolve only image version variables — gen_docker-compose uses raw sed to extract
# image names and cannot handle unresolved shell variables. Only resolve image tag
# vars so runtime vars (ADSBLOL_ENABLED, RECEIVER_LAT, etc.) remain as variable
# references and are resolved from .env at deploy time.
sed -e 's/\${BLAH2_V:-\([^}]*\)}/\1/g' \
    -e 's/\${TAR1090_V:-\([^}]*\)}/\1/g' \
    -e 's/\${ADSB2DD_V:-\([^}]*\)}/\1/g' \
    -e 's/\${CONFIG_MERGER_V:-\([^}]*\)}/\1/g' \
    -e 's/\${SPECTRUM_V:-\([^}]*\)}/\1/g' \
    -e 's/\${RETINA_TRACKER_V:-\([^}]*\)}/\1/g' \
    -e 's/\${TELEMETRY_V:-\([^}]*\)}/\1/g' \
    "${COMPOSE_FILE}" > "${MANIFEST_DIR}/docker-compose.yaml"

# Every image tag must be a literal by this point. The list above is by hand,
# so adding a service to docker-compose.yml without adding its clause here
# leaves a ${VAR:-default} that skopeo receives as a literal tag — the artifact
# either fails to build or installs a service that can never start. Cheaper to
# fail here, with the name of the variable that was missed.
if unresolved=$(grep -nE '^\s+image:.*\$\{' "${MANIFEST_DIR}/docker-compose.yaml"); then
    echo "Error: unresolved image tag variables in the generated manifest:" >&2
    echo "${unresolved}" >&2
    echo "Add a matching -e clause above for each." >&2
    exit 1
fi

SCRIPT_DIR="$(dirname "$0")/mender-state-scripts"

# Build artifact — gen_docker-compose pulls images via skopeo automatically
gen_docker-compose \
    --artifact-name "${ARTIFACT_NAME}-${VERSION}" \
    --device-type "${DEVICE_TYPE}" \
    --architecture arm64 \
    --manifests-dir "${MANIFEST_DIR}" \
    --project-name "${ARTIFACT_NAME}" \
    --output-path "${ARTIFACT_OUT}" \
    -- \
    --software-filesystem data-docker \
    --clears-provides "rootfs-image.retina-node.version" \
    --script "${SCRIPT_DIR}/ArtifactInstall_Enter_00_retina_state" \
    --script "${SCRIPT_DIR}/ArtifactCommit_Leave_00_retina_state" \
    --script "${SCRIPT_DIR}/ArtifactFailure_Enter_00_retina_state"

# Validate artifact
mender-artifact validate "${ARTIFACT_OUT}" || {
  echo "Error: Artifact validation failed"
  exit 1
}

# Check size
SIZE=$(stat -c%s "${ARTIFACT_OUT}" 2>/dev/null || stat -f%z "${ARTIFACT_OUT}")
SIZE_MB=$((SIZE / 1024 / 1024))

# Write metadata
cat > "${METADATA_OUT}" <<EOF
{
  "stack_version": "${VERSION}",
  "artifact_name": "${ARTIFACT_NAME}-${VERSION}",
  "device_type": "${DEVICE_TYPE}",
  "artifact_size_bytes": ${SIZE},
  "artifact_size_mb": ${SIZE_MB},
  "built_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_sha": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
}
EOF

echo "Done: ${ARTIFACT_OUT} (${SIZE_MB}MB)"

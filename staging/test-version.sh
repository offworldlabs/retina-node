#!/usr/bin/env bash
# Quick script to test a specific package version
# Usage: ./test-version.sh blah2 v0.3.5
#        ./test-version.sh adsb2dd v0.1.4

set -euo pipefail

COMPONENT=${1:-}
VERSION=${2:-}

usage() {
  cat <<EOF
Usage: $0 <component> <version>

Test a specific component version in staging.

Components:
  blah2      - blah2-arm package (BLAH2_V)
  adsb2dd    - adsb2dd package (ADSB2DD_V)
  tar1090    - tar1090 package (TAR1090_V)
  config     - config-merger (CONFIG_MERGER_V)

Examples:
  $0 blah2 v0.3.5
  $0 adsb2dd v0.1.4
  $0 tar1090 v0.2.1

This script:
1. Updates .env.staging with the new version
2. Pulls the new image
3. Restarts affected services
4. Shows logs for verification
EOF
  exit 1
}

if [ -z "$COMPONENT" ] || [ -z "$VERSION" ]; then
  usage
fi

# Map component to env var
case "$COMPONENT" in
  blah2)
    ENV_VAR="BLAH2_V"
    SERVICES="blah2_api blah2_web blah2_host"
    ;;
  adsb2dd)
    ENV_VAR="ADSB2DD_V"
    SERVICES="adsb2dd"
    ;;
  tar1090)
    ENV_VAR="TAR1090_V"
    SERVICES="tar1090"
    ;;
  config)
    ENV_VAR="CONFIG_MERGER_V"
    SERVICES="config-merger"
    ;;
  *)
    echo "Error: Unknown component '$COMPONENT'"
    usage
    ;;
esac

echo "Testing $COMPONENT $VERSION"
echo ""

# Update .env.staging
if [ ! -f .env.staging ]; then
  echo "Error: .env.staging not found. Run ./setup.sh first."
  exit 1
fi

echo "1. Updating .env.staging..."
if grep -q "^${ENV_VAR}=" .env.staging; then
  sed -i.bak "s/^${ENV_VAR}=.*/${ENV_VAR}=${VERSION}/" .env.staging
else
  echo "${ENV_VAR}=${VERSION}" >> .env.staging
fi
rm -f .env.staging.bak
echo "   Set ${ENV_VAR}=${VERSION}"

# Pull new image
echo ""
echo "2. Pulling new image..."
docker compose -f docker-compose.staging.yml --env-file .env.staging pull $SERVICES

# Restart services
echo ""
echo "3. Restarting services..."
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --force-recreate $SERVICES

# Show status
echo ""
echo "4. Service status..."
docker compose -f docker-compose.staging.yml ps $SERVICES

# Show logs
echo ""
echo "5. Recent logs (Ctrl-C to exit)..."
sleep 2
docker compose -f docker-compose.staging.yml logs -f --tail=50 $SERVICES

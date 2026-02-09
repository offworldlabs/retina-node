#!/usr/bin/env bash
# Setup staging environment for retina-node on x86_64 server
# Enables ARM64 container execution via QEMU userspace emulation
set -euo pipefail

echo "=== Retina Node Staging Setup ==="
echo "Setting up ARM64 emulation on x86_64 host"
echo ""

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
  echo "Warning: This script is designed for x86_64 hosts. Current: $ARCH"
fi

# Install QEMU and binfmt support
echo "Installing QEMU for ARM64 emulation..."
sudo apt-get update
sudo apt-get install -y qemu-user-static binfmt-support

# Register ARM64 binary format handlers
echo "Registering ARM64 binary formats..."
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Verify ARM64 support
echo ""
echo "Verifying ARM64 support..."
if docker run --rm --platform linux/arm64 arm64v8/alpine uname -m | grep -q aarch64; then
  echo "✓ ARM64 emulation working"
else
  echo "✗ ARM64 emulation failed"
  exit 1
fi

# Create staging directory structure
echo ""
echo "Creating staging directories..."
mkdir -p config data/blah2/save data/blah2/test

# Copy configuration templates
if [ ! -f config/user.yml ]; then
  echo "Creating default staging config..."
  cat > config/user.yml <<'EOF'
# Staging environment configuration
# Pulls data from radar3.retnode.com production node

location:
  rx:
    latitude: 33.939182
    longitude: -84.65191
    altitude: 320
    name: "radar3-rx"
  tx:
    latitude: 33.939182
    longitude: -84.331844
    altitude: 650
    name: "WXIA HDTV"

# Note: Network IPs will be overridden by .env.staging
# to point to public radar3 endpoints
EOF
fi

# Create .env file
if [ ! -f .env.staging ]; then
  echo "Creating .env.staging..."
  cat > .env.staging <<'EOF'
# Staging environment variables
# Run on x86_64 host with ARM64 emulation

# Skip config-merger (use manual config)
SKIP_CONFIG_MERGER=true

# Override paths for staging
CONFIG_DIR=./config
DATA_DIR=./data
MENDER_APP_DIR=./manifests
MENDER_DATA_DIR=./manifests

# Package versions (override these when testing new versions)
BLAH2_V=v0.3.4
TAR1090_V=v0.2.0
ADSB2DD_V=v0.1.3
CONFIG_MERGER_V=v0.3.3

# Service ports (avoid conflicts with other services)
BLAH2_WEB_PORT=49152
BLAH2_HOST_PORT=8080
TAR1090_PORT=8078

# Location (radar3)
RECEIVER_LAT=33.939182
RECEIVER_LON=-84.65191
RECEIVER_ALT=320
TZ=America/New_York

# ADS-B feed configuration
# Point to radar3's public endpoints
READSB_NET_CONNECTOR=radar3.retnode.com,30005,beast_in
ADSBLOL_ENABLED=true
ADSBLOL_RADIUS=40
EOF
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review and edit config/user.yml for your needs"
echo "2. Update .env.staging with package versions to test"
echo "3. Run: docker compose -f docker-compose.staging.yml --env-file .env.staging up -d"
echo "4. Access services:"
echo "   - blah2 UI: http://localhost:49152"
echo "   - tar1090: http://localhost:8078"
echo "   - adsb2dd: http://localhost:49155"

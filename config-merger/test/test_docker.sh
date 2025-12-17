#!/bin/bash
# Quick Dockerfile test - builds image and runs a basic merge

set -e

cd "$(dirname "$0")/../.."

echo "Building config-merger image..."
docker build -t retina-config-merger:test -f config-merger/Dockerfile .

echo "Running basic merge test..."
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

mkdir -p "$TEST_DIR/config"
echo "network:" > "$TEST_DIR/config/user.yml"
echo "  node_id: test" >> "$TEST_DIR/config/user.yml"

docker run --rm -v "$TEST_DIR/config:/data/retina-node/config" retina-config-merger:test

if [ -f "$TEST_DIR/config/config.yml" ]; then
  echo "✓ Success - config.yml created"
else
  echo "✗ Failed - config.yml not created"
  exit 1
fi

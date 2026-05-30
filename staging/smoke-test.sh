#!/usr/bin/env bash
# Smoke tests for staging environment
# Verifies all services are healthy and responding

set -euo pipefail

FAILED=0

test_endpoint() {
  local name=$1
  local url=$2
  local expected=${3:-}

  echo -n "Testing $name... "

  if response=$(curl -sf --max-time 5 "$url" 2>&1); then
    if [ -n "$expected" ]; then
      if echo "$response" | grep -q "$expected"; then
        echo "✓"
      else
        echo "✗ (unexpected response)"
        FAILED=$((FAILED + 1))
      fi
    else
      echo "✓"
    fi
  else
    echo "✗ (connection failed)"
    FAILED=$((FAILED + 1))
  fi
}

test_json_endpoint() {
  local name=$1
  local url=$2
  local jq_filter=$3
  local min_value=${4:-0}

  echo -n "Testing $name... "

  if ! command -v jq &>/dev/null; then
    echo "⚠ (jq not installed)"
    return
  fi

  if response=$(curl -sf --max-time 5 "$url" 2>&1); then
    if value=$(echo "$response" | jq -r "$jq_filter" 2>/dev/null); then
      if [ "$value" -ge "$min_value" ] 2>/dev/null; then
        echo "✓ (value: $value)"
      else
        echo "⚠ (value: $value, expected >= $min_value)"
      fi
    else
      echo "✗ (invalid JSON)"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "✗ (connection failed)"
    FAILED=$((FAILED + 1))
  fi
}

echo "=== Retina Node Staging Smoke Tests ==="
echo ""

# Check containers are running
echo "Checking containers..."
RUNNING=$(docker compose -f docker-compose.staging.yml ps --filter "status=running" -q | wc -l)
EXPECTED=6  # blah2_api, blah2_web, blah2_host, tar1090, adsb2dd, (config-merger exits)
if [ "$RUNNING" -ge $((EXPECTED - 1)) ]; then
  echo "✓ $RUNNING/$EXPECTED containers running"
else
  echo "✗ Only $RUNNING/$EXPECTED containers running"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "Testing web interfaces..."
test_endpoint "blah2 web UI" "http://localhost:49152" "<!DOCTYPE html>"
test_endpoint "blah2 host" "http://localhost:8080"
test_endpoint "tar1090" "http://localhost:8078" "tar1090"

echo ""
echo "Testing APIs..."
test_endpoint "blah2 API config" "http://localhost:3000/api/config"
test_endpoint "adsb2dd API" "http://localhost:49155/api"

echo ""
echo "Testing data feeds..."
test_json_endpoint "tar1090 aircraft" "http://localhost:8078/data/aircraft.json" ".aircraft | length" 0
test_json_endpoint "adsb2dd targets" "http://localhost:49155/api" "keys | length" 0

echo ""
echo "Checking logs for errors..."
ERRORS=$(docker compose -f docker-compose.staging.yml logs --since 5m 2>&1 | grep -ci "error" || true)
if [ "$ERRORS" -eq 0 ]; then
  echo "✓ No errors in recent logs"
else
  echo "⚠ Found $ERRORS error messages in logs (review manually)"
fi

echo ""
echo "==================================="
if [ $FAILED -eq 0 ]; then
  echo "✓ All tests passed!"
  exit 0
else
  echo "✗ $FAILED test(s) failed"
  exit 1
fi

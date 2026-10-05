# Retina Node Staging Environment

Staging environment for testing retina-node deployments before production. Runs ARM64 containers on x86_64 hosts using QEMU emulation.

## Overview

**Purpose**: Catch integration bugs and configuration errors before deploying to production Raspberry Pi nodes.

**Architecture**:
- x86_64 Hetzner server running Ubuntu
- QEMU userspace emulation for ARM64 containers
- Services pull real data from radar3.retnode.com
- Tests: blah2 API/web, tar1090, adsb2dd (blah2 core disabled - requires SDR hardware)

**What This Tests**:
- ✅ ARM64 container compatibility
- ✅ Service integration and networking
- ✅ Configuration changes
- ✅ Web interfaces and APIs
- ✅ Data pipeline: ADS-B → tar1090 → adsb2dd
- ❌ Actual SDR radar processing (requires hardware)

**What This Doesn't Test**:
- Mender deployment flow (see "Full Mender Testing" section)
- Hardware-specific issues (SDR drivers, USB)
- Performance under load

## Quick Start

```bash
# 1. Clone repo and navigate to staging
cd retina-node/staging

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Merge configuration
chmod +x merge-config.sh
./merge-config.sh

# 4. Start services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 5. Verify
docker compose -f docker-compose.staging.yml ps
curl http://localhost:8078  # tar1090
curl http://localhost:49152  # blah2 web
```

## Detailed Setup

### Prerequisites

- x86_64 Linux server (Ubuntu 22.04+ recommended)
- Docker and Docker Compose installed
- Minimum 4GB RAM, 20GB disk
- Python 3 with PyYAML (`pip3 install pyyaml`)
- Network access to radar3.retnode.com

### Step 1: Install QEMU Support

Run the setup script to install QEMU and register ARM64 binary formats:

```bash
cd retina-node/staging
chmod +x setup.sh
./setup.sh
```

This installs:
- `qemu-user-static` - ARM64 userspace emulation
- `binfmt-support` - Binary format handlers
- Registers ARM64 support with Docker

**Verify ARM64 works**:
```bash
docker run --rm --platform linux/arm64 arm64v8/alpine uname -m
# Should output: aarch64
```

### Step 2: Configure Environment

Edit `.env.staging` to set package versions to test:

```bash
nano .env.staging
```

Key variables:
```bash
# Package versions to test
BLAH2_V=v0.3.5        # Update this when testing new blah2 builds
ADSB2DD_V=v0.1.4      # Update this when testing new adsb2dd builds
TAR1090_V=v0.2.0

# Service ports (defaults work for single staging instance)
BLAH2_WEB_PORT=49152
TAR1090_PORT=8078

# Location (radar3 - already configured)
RECEIVER_LAT=33.939182
RECEIVER_LON=-84.65191
RECEIVER_ALT=320

# ADS-B feed from radar3
READSB_NET_CONNECTOR=radar3.retnode.com,30005,beast_in
```

### Step 3: Merge Configuration

Generate the merged config file:

```bash
chmod +x merge-config.sh
./merge-config.sh
```

This creates `config/config.yml` by merging:
- `../config/default.yml` (base defaults)
- `config/user.yml` (staging overrides)
- `../config/forced.yml` (forced values)

**Optional**: Edit `config/user.yml` to override specific settings.

### Step 4: Start Services

```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

**First run takes 5-10 minutes** - Docker pulls ARM64 images and QEMU emulates them.

**Check status**:
```bash
docker compose -f docker-compose.staging.yml ps
docker compose -f docker-compose.staging.yml logs -f
```

### Step 5: Verify Services

**Web Interfaces**:
- blah2: http://localhost:49152
- tar1090: http://localhost:8078
- adsb2dd API: http://localhost:49155/api

**Health Checks**:
```bash
# Check tar1090 is receiving ADS-B
curl -s http://localhost:8078/data/aircraft.json | jq '.aircraft | length'

# Check adsb2dd is processing
curl -s http://localhost:49155/api | jq 'keys | length'

# Check all containers running
docker compose -f docker-compose.staging.yml ps
```

**Expected Output**:
- tar1090 shows aircraft from radar3's area (Georgia)
- adsb2dd returns delay-Doppler data
- blah2 web UI loads (but shows no radar data - normal without SDR)

## Testing Workflow

### Testing New Package Versions

**Scenario**: You've built new blah2 v0.3.5 and want to test it before production.

```bash
# 1. Update version in .env.staging
nano .env.staging
# Change: BLAH2_V=v0.3.5

# 2. Pull new images and restart
docker compose -f docker-compose.staging.yml --env-file .env.staging pull
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --force-recreate

# 3. Watch for errors
docker compose -f docker-compose.staging.yml logs -f blah2_api blah2_web

# 4. Verify web interface
curl http://localhost:49152
# Or open in browser and click around

# 5. Check for breaking changes
docker compose -f docker-compose.staging.yml exec blah2_api node --version
docker compose -f docker-compose.staging.yml logs blah2_api | grep -i error
```

### Testing Configuration Changes

**Scenario**: You've modified default.yml or forced.yml.

```bash
# 1. Merge updated config
./merge-config.sh

# 2. Restart services to pick up config
docker compose -f docker-compose.staging.yml --env-file .env.staging restart

# 3. Verify config applied
docker compose -f docker-compose.staging.yml exec blah2_api cat /usr/src/app/config/config.yml
```

### Visual Testing with Browser

For UI changes, use Claude in Chrome or manual testing:

```bash
# Start services if not running
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Get your server's public IP
curl -4 ifconfig.me

# Open in browser:
# http://<server-ip>:49152  (blah2)
# http://<server-ip>:8078   (tar1090)
```

**Firewall Note**: Open ports 49152, 8078, 49155 if testing remotely.

### Automated Integration Tests

Basic smoke tests:

```bash
#!/bin/bash
# save as test-staging.sh

set -e

echo "Running staging integration tests..."

# Test tar1090
echo "✓ Testing tar1090..."
AIRCRAFT=$(curl -s http://localhost:8078/data/aircraft.json | jq '.aircraft | length')
if [ "$AIRCRAFT" -gt 0 ]; then
  echo "  ✓ Receiving $AIRCRAFT aircraft"
else
  echo "  ⚠ No aircraft received (might be normal if radar3 area is empty)"
fi

# Test adsb2dd
echo "✓ Testing adsb2dd..."
TARGETS=$(curl -s http://localhost:49155/api | jq 'keys | length')
echo "  ✓ Processing $TARGETS targets"

# Test blah2 API
echo "✓ Testing blah2 API..."
curl -f http://localhost:3000/api/config >/dev/null
echo "  ✓ API responding"

# Test blah2 web
echo "✓ Testing blah2 web..."
curl -f http://localhost:49152 >/dev/null
echo "  ✓ Web UI responding"

echo ""
echo "All tests passed! ✓"
```

## Common Issues

### Services Won't Start

**Check ARM64 support**:
```bash
docker run --rm --platform linux/arm64 arm64v8/alpine uname -m
```

If this fails, re-run setup:
```bash
./setup.sh
```

### Slow Performance

ARM64 emulation is inherently slower than native. Typical performance:
- Container startup: 2-5x slower
- Runtime: 1.5-3x slower
- Acceptable for testing, not for production loads

**Improve performance**:
- Use server with more CPU cores
- Reduce number of concurrent containers
- Use caching for frequent rebuilds

### Can't Pull Images

**Authentication required**:
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Port Conflicts

If ports 8078, 49152, 49155 are in use:

```bash
# Edit .env.staging to use different ports
nano .env.staging

# Example:
BLAH2_WEB_PORT=59152
TAR1090_PORT=58078
```

### tar1090 Shows No Aircraft

**Check ADS-B feed**:
```bash
# Verify connectivity to radar3
curl -v telnet://radar3.retnode.com:30005

# Check tar1090 logs
docker compose -f docker-compose.staging.yml logs tar1090 | grep -i beast
```

If radar3 feed is down, enable adsb.lol fallback in `.env.staging`:
```bash
ADSBLOL_ENABLED=true
ADSBLOL_RADIUS=40
```

## Full Mender Testing (Advanced)

For testing the complete Mender deployment flow, use a full ARM64 VM:

### Option B: QEMU ARM64 VM

**When to use**: Before deploying to production to test Mender artifact deployment.

**Setup** (brief - requires more expertise):
```bash
# Install QEMU system emulation
sudo apt install qemu-system-aarch64

# Create ARM64 VM with owl-os
# Follow owl-os installation guide
# Configure Mender client to point to your Mender server

# Deploy artifact via Mender dashboard
# Verify deployment succeeds
```

**Pros**:
- Tests full Mender deployment flow
- Identical to production environment

**Cons**:
- Slow (full system emulation)
- Complex setup (requires VM management)
- Use sparingly (once before major releases)

**Recommendation**: Use Docker staging (Option A) for daily testing, VM testing (Option B) only for critical pre-production validation.

## Maintenance

### Updating Staging

Pull latest retina-node changes:
```bash
cd retina-node
git pull
cd staging
./merge-config.sh
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --force-recreate
```

### Cleaning Up

Remove all staging containers and volumes:
```bash
docker compose -f docker-compose.staging.yml down -v
rm -rf data/ config/config.yml
```

### Disk Space

Check Docker disk usage:
```bash
docker system df
docker image prune -a  # Remove unused images
```

## Next Steps

After staging tests pass:

1. **Tag new version** in source repos (blah2-arm, adsb2dd)
2. **GitHub Actions builds** Mender artifact
3. **Download artifact** from GitHub releases
4. **Upload to Mender dashboard**
5. **Deploy to production** device group
6. **Monitor deployment** via Mender
7. **Verify production** node health

## References

- [retina-node README](../README.md) - Main documentation
- [STANDALONE.md](../STANDALONE.md) - Standalone deployment
- [owl-os](https://github.com/offworldlabs/owl-os) - Base OS for production nodes
- [Mender Documentation](https://docs.mender.io/) - OTA deployment platform

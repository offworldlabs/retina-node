# Standalone Deployment

Run the retina passive radar stack without Mender infrastructure (for advanced users and devs).

This is useful for a fast dev/testing loop without using Mender deployment infrastructure to test changes to services running on the node. Or if you plan on running the retina-stack on your own hardware and don't want to opt in to Mender.

[Owl-os](https://github.com/offworldlabs/owl-os) can be used as a base OS image (recommended - saves installing system requirements) or any Linux system (not all tested but should work in theory).

If you want a managed node as part of the retina-network, this approach is not recommended.

Uses a .env file to override paths and image versions in the shared docker-compose.yml for local use.

## Prerequisites

- Linux system (x86_64 or ARM64)
- Docker & Docker Compose
- SDRplay RSPduo with drivers installed
- SDRplay API library at `/usr/local/lib/libsdrplay_api.so.3.15`

## System requirements (if not using owl-os), install:

TODO: Document system requirements for non-owl-os systems

> [!WARNING]
> **If running on owl-os with Mender-deployed services**, stop them first:
> ```bash
> cd /data/mender-app/retina-node/manifests
> docker compose -p retina-node down
> ```
> To switch back to Mender-deployed services later:
> ```bash
> cd /opt/retina-standalone
> docker compose down
> cd /data/mender-app/retina-node/manifests
> docker compose -p retina-node up -d
> ```

## Quick Start

```bash
# Clone the repo
sudo git clone https://github.com/offworldlabs/retina-node.git /opt/retina-standalone
# Or clone a specific release
sudo git clone -b v0.3.0 https://github.com/offworldlabs/retina-node.git /opt/retina-standalone
cd /opt/retina-standalone

# Set up config
sudo cp .env.example .env
sudo cp config/default.yml config/config.yml

# Edit your config
sudo nano config/config.yml  # Set location, frequency, etc.
sudo nano .env               # Set location for tar1090 map

# Start
sudo docker compose up -d
```

## Web Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| blah2 | http://retina.local:49152/ | Passive radar display |
| tar1090 | http://retina.local:8078/ | ADS-B aircraft map |
| adsb2dd | http://retina.local:49155/ | Delay-Doppler truth overlay |

Note: retina-gui (http://retina.local/) is not fully supported when running standalone (yet), config is not editable via the GUI and should be done manually.

## Development Workflow

For testing container changes without Mender:

1. **Build container images** (in the subcomponent repo, e.g. `blah2-arm`) - pushes to GHCR:
   - **Tagged release**: Push `v0.3.0` or `v0.3.0-rc1` tag - auto builds
   - **Dev testing**: Manual dispatch from Actions tab with `dev` tag (can re-run multiple times)

2. **Update `.env`** with the new image version you want to test:
   ```bash
   BLAH2_V=dev
   # or a specific version
   BLAH2_V=v0.3.0
   ```

3. **Stop, pull and restart**:
   ```bash
   sudo docker compose down
   sudo docker compose pull
   sudo docker compose up -d
   ```

4. **Check status and logs**:
   ```bash
   sudo docker ps
   sudo docker logs -f blah2
   ```

## Configuration

Config is split between two files: `.env` for tar1090 and docker compose settings, and `config.yml` for blah2 settings. 

### `.env` - Environment Settings

```bash
# Standalone mode (required)
SKIP_CONFIG_MERGER=true # We ignore this container as it is for fleet config management
CONFIG_DIR=./config
DATA_DIR=./data

# ADSB Location (should match config/config.yml)
RECEIVER_LAT=37.7644
RECEIVER_LON=-122.3954
RECEIVER_ALT=23

# ADS-B settings
ADSBLOL_ENABLED=true
ADSBLOL_RADIUS=40

# External ADS-B feed (uncomment if you have a local source)
# READSB_NET_CONNECTOR=192.168.1.100,30005,beast_in

# Image versions (uncomment to override)
# BLAH2_V=dev
# TAR1090_V=v0.2.0
# ADSB2DD_V=v0.1.3
```

For development, uncomment and edit the image versions in `.env` to quickly switch between versions without modifying docker-compose.yml.

### `config/config.yml` - blah2 Settings


```yaml
capture:
  type: "RSPduo"              # SDR type
  fc: 250000000               # Reference signal frequency (Hz)
  fs: 2000000                 # Sample rate

process:
  reference:
    fc: 250000000             # Reference frequency (same as capture.fc)
  surveillance:
    fc: 250000000             # Surveillance frequency (can be same or different)

location:
  rx:
    latitude: 37.7644         # Your receiver location
    longitude: -122.3954
    altitude: 23

  ...
```

See [blah2-arm documentation](https://github.com/offworldlabs/blah2-arm) for full config options.

## Commands

From the install location (`/opt/retina-standalone`):

```bash
# Start all services
sudo docker compose up -d

# Stop all services
sudo docker compose down

# View logs
sudo docker logs blah2 --tail 50
sudo docker logs tar1090 --tail 50

# Restart after config change
sudo docker compose restart blah2

# Update to latest images
sudo docker compose pull
sudo docker compose up -d
```

## Updating

```bash
# Pull latest
sudo git pull
sudo docker compose pull
sudo docker compose up -d

# Or update to a specific release
sudo git fetch --tags
sudo git checkout v0.4.0
sudo docker compose pull
sudo docker compose up -d
```

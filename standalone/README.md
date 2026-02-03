# Standalone Deployment

Run the retina passive radar stack without Mender infrastructure (for advanced users and devs).

This is useful for a fast dev/testing loop without using Mender deployment infrastructure to test changes to services running on the node.

[Owl-os](https://github.com/offworldlabs/owl-os) can be used as a base OS image (recommended - saves installing system requirements) or any Linux system (not all tested but should work in theory).

If you want a managed node as part of the retina-network, this approach is not recommended.

```
standalone/
├── .env                 # Image tags, location settings for tar1090
├── config/
│   └── config.yml       # blah2 SDR/frequency config/ location
├── data/
│   └── blah2/save/      # Saved detections (created on first run)
└── docker-compose.yml
```

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
> sudo docker compose -p retina-node down
> ```
> To switch back to Mender-deployed services later:
> ```bash
> cd /opt/retina-standalone/standalone
> sudo docker compose down
> cd /data/mender-app/retina-node/manifests
> sudo docker compose -p retina-node up -d
> ```

## Quick Start

```bash
# Clone the repo (latest dev)
sudo git clone https://github.com/offworldlabs/retina-node.git /opt/retina-standalone

# Or clone a stable, specific version
sudo git clone --branch v0.3.3 https://github.com/offworldlabs/retina-node.git /opt/retina-standalone

cd /opt/retina-standalone/standalone

# Edit your location (for ADS-B map)
sudo nano .env

# Edit blah2 config (SDR, frequencies, location)
sudo nano config/config.yml

# Start
sudo docker compose up -d
```

## Web Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| blah2 | http://retina.local:49152/ | Passive radar display |
| tar1090 | http://retina.local:8078/ | ADS-B aircraft map |
| adsb2dd | http://retina.local:49155/ | Delay-Doppler truth overlay |

Note: retina-gui is not fully supported when running standalone, config is not editable via the GUI.

## Development Workflow

For testing container changes without Mender:

1. **Push changes to your branch** - GHA builds and pushes to GHCR with `dev` tag (or create a new tag like `v0.3.0` for a versioned release)

2. **Update `.env`** with the tag you want to test:
   ```bash
   BLAH2_TAG=dev
   # or a specific version
   BLAH2_TAG=v0.3.0
   ```

3. **Stop, pull and restart**:
   ```bash
   sudo docker compose down
   sudo docker compose pull
   sudo docker compose up -d
   ```

4. **Check logs**:
   ```bash
   sudo docker logs -f blah2
   ```

Use `dev` tag for latest builds, or pin to a specific version for stability.

## Configuration

Config is split between two files: `.env` for tar1090 and docker compose settings, and `config.yml` for blah2 settings. 

### `.env` - Environment Settings

```bash
# --- Image tags (optional) ---
# Uncomment to override default versions for dev/testing
# BLAH2_TAG=dev
# TAR1090_TAG=v0.2.0
# ADSB2DD_TAG=v0.1.3

# --- tar1090 location settings ---
RECEIVER_LAT=51.5074
RECEIVER_LON=-0.1278
RECEIVER_ALT=10

# --- tar1090 ADS-B settings ---

# External ADS-B feed (optional) - format: host,port,protocol
# Example: 192.168.1.100,30005,beast_in
READSB_NET_CONNECTOR=

# adsb.lol fallback - fetches ADS-B data when no local feed available
ADSBLOL_ENABLED=true
ADSBLOL_RADIUS=40
```

For development, uncomment and edit the image tags in `.env` to quickly switch between versions without modifying docker-compose.yml.

### `config/config.yml` - blah2 Settings

Key settings to configure:

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
    latitude: 51.5074         # Your receiver location
    longitude: -0.1278
    altitude: 10
```

See [blah2 documentation](https://github.com/30hours/blah2) for full config options.

## Commands

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
cd /opt/retina-standalone
sudo git pull                 # Get latest compose/config
cd standalone
sudo docker compose pull           # Pull new images
sudo docker compose up -d          # Restart with new images
```




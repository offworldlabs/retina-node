# Standalone Deployment

Run the retina passive radar stack without owl-os/Mender infrastructure.

## Prerequisites

- Linux system (x86_64 or ARM64)
- Docker & Docker Compose
- SDRplay RSPduo with drivers installed
- SDRplay API library at `/usr/local/lib/libsdrplay_api.so.3.15`

## Quick Start

```bash
# Clone the repo
git clone https://github.com/offworldlabs/retina-node.git /opt/retina
cd /opt/retina/standalone

# Edit your location (for ADS-B map)
nano .env

# Edit blah2 config (SDR, frequencies)
nano config/config.yml

# Start
docker compose up -d
```

## Web Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| blah2 | http://localhost:8080 | Passive radar display |
| tar1090 | http://localhost:8078 | ADS-B aircraft map |

## Configuration

### `.env` - Environment Settings

```bash
# Image versions
BLAH2_TAG=dev              # or v0.2.9 for stable
TAR1090_TAG=v0.2.0
ADSB2DD_TAG=v0.1.3

# Your location (for ADS-B map centering)
RECEIVER_LAT=51.5074
RECEIVER_LON=-0.1278
RECEIVER_ALT=10

# ADS-B fallback (fetches aircraft from adsb.lol when no local feed)
ADSBLOL_ENABLED=true
ADSBLOL_RADIUS=40
```

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
docker compose up -d

# Stop all services
docker compose down

# View logs
docker logs blah2 --tail 50
docker logs tar1090 --tail 50

# Restart after config change
docker compose restart blah2

# Update to latest images
docker compose pull
docker compose up -d
```

## Updating

```bash
cd /opt/retina
git pull                      # Get latest compose/config
cd standalone
docker compose pull           # Pull new images
docker compose up -d          # Restart with new images
```

## Version Pinning

For stable deployments, pin image versions in `.env`:

```bash
BLAH2_TAG=v0.2.9
TAR1090_TAG=v0.2.0
ADSB2DD_TAG=v0.1.3
```

Use `dev` tag for latest development builds.

## Troubleshooting

### blah2 won't start
```bash
# Check logs
docker logs blah2

# Common issues:
# - SDRplay driver not installed
# - Config file syntax error
# - USB permissions (try: sudo docker compose up -d)
```

### No aircraft on tar1090
```bash
# Check if adsb.lol fallback is working
docker logs tar1090 | grep adsb.lol

# Verify location is set
docker inspect tar1090 --format='{{range .Config.Env}}{{println .}}{{end}}' | grep RECEIVER
```

### SDRplay not detected
```bash
# Restart SDRplay service on host
sudo systemctl restart sdrplay

# Check USB device is visible
lsusb | grep SDR
```

## Directory Structure

```
standalone/
├── .env                 # Environment config (image tags, location)
├── config/
│   └── config.yml       # blah2 configuration
├── data/
│   └── blah2/
│       └── save/        # Saved detections (persistent)
└── docker-compose.yml   # Service definitions
```

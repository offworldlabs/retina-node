# retina-node

Orchestrator repository for Retina passive radar nodes. Manages docker-compose configuration and Mender OTA artifact generation.

Deploy to nodes running owl-os via the Mender dashboard.

## Web Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| blah2 | `http://<PI_IP>:8080` (mDNS pending) | Passive radar UI |
| tar1090 | `http://<PI_IP>` or `http://retina.local` | ADS-B aircraft map |
| adsb2dd | `http://<PI_IP>:49155` or `http://retina.local:49155` | Delay-Doppler converter |

## Node Access

Access nodes via Mender troubleshooting terminal.

```
/data/
├── mender-app/retina-node/manifests/
│   └── docker-compose.yaml    # Deployed compose file
│
└── retina-node/
    ├── config/
    │   ├── user.yml           # User config overrides (edit this)
    │   ├── config.yml         # Merged config (auto-generated)
    │   └── tar1090.env        # tar1090 env vars (auto-generated)
    └── blah2/
        ├── save/              # Persistent radar data
        ├── script/            # Runtime scripts
        └── test/              # Test data
```

## Configuration

Config-merger generates config files at startup by merging:

```
default.yml → user.yml → forced.yml
```

Later files override earlier ones.

### Editing Config on a Node

> **TODO:** Web UI for configuration management.

1. Edit user.yml (not config.yml):
   ```bash
   nano /data/retina-node/config/user.yml
   ```

2. Restart stack to regenerate merged config:
   ```bash
   cd /data/mender-app/retina-node/manifests && sudo docker compose down --remove-orphans && sudo docker compose up -d
   ```

3. Verify:
   ```bash
   cat /data/retina-node/config/config.yml
   ```

### Editing Default/Forced Config

Edit files in `config-merger/config/` directory in this repo, then rebuild and deploy.

## Creating a Release

1. Update `docker-compose.yml` with desired package versions
2. Tag with `git tag vX.X.X` and push
3. CI workflow generates Mender artifact and uploads to dashboard

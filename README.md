# retina-node

Orchestrator repository for Retina passive radar nodes. Manages docker-compose configuration and Mender OTA update artifact generation for all node packages.

## Config Merger

The config-merger container generates configuration files at startup by merging:

```
default.yml → user.yml → forced.yml
```

Later files override earlier ones. User overrides persist in `/data/retina-node/config/user.yml`.

**Outputs** (to `/data/retina-node/config/`):
- `config.yml` - Merged config for blah2
- `tar1090.env` - Environment variables for tar1090-node

# Staging Quick Reference

## Initial Setup (One Time)

```bash
cd retina-node/staging
./setup.sh                # Install QEMU, create directories
./merge-config.sh         # Generate config.yml
```

## Start Services

```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

## Test New Version

```bash
# Quick test of specific version
./test-version.sh blah2 v0.3.5
./test-version.sh adsb2dd v0.1.4

# Or manually:
nano .env.staging         # Update version
docker compose -f docker-compose.staging.yml --env-file .env.staging pull
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d --force-recreate
```

## Check Status

```bash
# Service status
docker compose -f docker-compose.staging.yml ps

# Recent logs
docker compose -f docker-compose.staging.yml logs -f --tail=50

# Specific service logs
docker compose -f docker-compose.staging.yml logs -f blah2_api

# Run smoke tests
./smoke-test.sh
```

## Access Services

- blah2 UI: http://localhost:49152
- tar1090: http://localhost:8078
- adsb2dd: http://localhost:49155/api
- blah2 API: http://localhost:3000/api/config

## Quick Health Checks

```bash
# Check containers running
docker compose -f docker-compose.staging.yml ps

# Check tar1090 receiving aircraft
curl -s http://localhost:8078/data/aircraft.json | jq '.aircraft | length'

# Check adsb2dd processing
curl -s http://localhost:49155/api | jq 'keys | length'

# Check for errors
docker compose -f docker-compose.staging.yml logs --since 5m | grep -i error
```

## Configuration Changes

```bash
nano config/user.yml      # Edit staging config
./merge-config.sh         # Regenerate config.yml
docker compose -f docker-compose.staging.yml restart
```

## Stop/Cleanup

```bash
# Stop services
docker compose -f docker-compose.staging.yml down

# Stop and remove volumes
docker compose -f docker-compose.staging.yml down -v

# Remove all staging data
rm -rf data/ config/config.yml
```

## Troubleshooting

```bash
# Check ARM64 support
docker run --rm --platform linux/arm64 arm64v8/alpine uname -m

# Restart QEMU support
./setup.sh

# Force recreate all services
docker compose -f docker-compose.staging.yml up -d --force-recreate

# Remove and rebuild everything
docker compose -f docker-compose.staging.yml down -v
docker system prune -a
./setup.sh
./merge-config.sh
docker compose -f docker-compose.staging.yml up -d
```

## Common Workflow

**Daily testing cycle**:
```bash
# 1. Update version
./test-version.sh blah2 v0.3.5

# 2. Run smoke tests
./smoke-test.sh

# 3. Visual testing (open in browser)
open http://localhost:49152
open http://localhost:8078

# 4. Check logs
docker compose -f docker-compose.staging.yml logs -f
```

**Before deploying to production**:
```bash
# 1. Test in staging
./test-version.sh blah2 v0.3.5
./smoke-test.sh

# 2. Visual verification
# Open web UIs and verify behavior

# 3. Let it run for a few hours
# Monitor logs for errors

# 4. If stable, proceed to production deployment via Mender
```

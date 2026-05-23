---
name: Environment Configuration Best Practices
description: "Use when: configuring or modifying .env files for Immich. Provides guidelines for secure secrets management, storage path configuration, version management, and environment-specific settings."
applyTo: ".env*"
---

# Environment Configuration Guide for Immich

## Overview

The `.env` file controls all runtime configuration for the Immich media server without requiring code changes or docker-compose.yml modifications. It's loaded by all services via the `env_file` directive.

## Critical Variables

### Storage Paths (REQUIRED - Customize Per System)

**UPLOAD_LOCATION**
```bash
UPLOAD_LOCATION=/rpool/data/immich/library
```
- Where Immich stores uploaded photos and videos
- Must be writable by Docker container (ensure permissions: `755` or `777`)
- Backup this directory regularly
- Should be on fast storage (SSD preferred)
- Can be on ZFS, RAID, or network storage (if properly mounted)

**DB_DATA_LOCATION**
```bash
DB_DATA_LOCATION=/rpool/data/immich/postgres
```
- Where PostgreSQL stores database files (metadata, user accounts, embeddings)
- ⚠️ **CRITICAL**: MUST be on fast SSD, NEVER on network share
- Database performance directly affects application responsiveness
- Backup this directory before any major Immich updates
- Should have at least 100GB free space (more for large libraries)

### Database Credentials (REQUIRED - Change in Production)

**DB_PASSWORD**
```bash
DB_PASSWORD=postgres
```
- ⚠️ **SECURITY**: Change from default `postgres` immediately in production
- Use only characters `A-Za-z0-9` (no special chars or spaces per Immich limitations)
- Generate: `openssl rand -base64 32 | tr -d '=' | cut -c1-32`
- Store securely; needed for database backups and recovery
- Example: `DB_PASSWORD=MySecure8CharPassword123`

**DB_USERNAME**
```bash
DB_USERNAME=postgres
```
- Usually left as `postgres` (default PostgreSQL admin user)
- Change only if you need multiple database users (advanced scenario)

**DB_DATABASE_NAME**
```bash
DB_DATABASE_NAME=immich
```
- Name of the database; usually `immich`
- Change only if running multiple Immich instances on same PostgreSQL server

### Immich Version Management

**IMMICH_VERSION**
```bash
IMMICH_VERSION=release
```
- `release`: Pulls latest stable release (default, auto-updates)
- `v1.71.0`: Pin to specific version for stability
- `latest`: Pulls development version (not recommended for production)

**When to pin versions:**
- Production environments (prevent breaking changes)
- Development/testing (reproducibility)
- Before major updates (test in staging first)

**How to update:**
1. Pin current version: `IMMICH_VERSION=v1.70.0`
2. Test upgrade in staging environment
3. Once verified, update to new version: `IMMICH_VERSION=v1.71.0`
4. Restart services: `docker-compose down && docker-compose up -d`

### Timezone (Optional)

**TZ**
```bash
# TZ=Etc/UTC
```
- Uncomment and set to your timezone for consistent logging and scheduling
- Format: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
- Examples:
  - `TZ=America/New_York`
  - `TZ=Europe/London`
  - `TZ=Asia/Tokyo`
  - `TZ=Etc/UTC` (default if unset)

## Advanced Configuration (Optional)

### Database Performance Tuning

Add to optimize PostgreSQL for your hardware:

```bash
# For HDD storage (slower performance expected)
DB_STORAGE_TYPE=HDD

# For high-traffic setups (add to docker-compose.yml, not .env)
POSTGRES_INITDB_ARGS='--data-checksums'
```

### Machine Learning Settings

Configure in `.env` for ML behavior:

```bash
# GPU acceleration (if hardware available)
# Add -cuda, -rocm, -openvino, -rknn, or -armnn to image tag in compose file

# Model cache location
# Set in docker-compose.yml volumes section (default: docker volume "model-cache")
```

### External Storage Integration

For Nextcloud or other media sources:
```bash
# Nextcloud mount path (edit in docker-compose.yml, not .env)
# /shared/nextcloud-photos:/usr/src/app/external/nextcloud:ro
```

## Environment-Specific Configurations

### Development Setup
```bash
UPLOAD_LOCATION=./test-media
DB_DATA_LOCATION=./test-db
DB_PASSWORD=testpass123
IMMICH_VERSION=release
```

### Staging/Testing
```bash
UPLOAD_LOCATION=/mnt/staging/immich/library
DB_DATA_LOCATION=/mnt/staging/immich/postgres
DB_PASSWORD=<strong-password>
IMMICH_VERSION=v1.70.0  # Pin to stable version
TZ=Etc/UTC
```

### Production
```bash
UPLOAD_LOCATION=/fast-ssd-mount/immich/library
DB_DATA_LOCATION=/fast-ssd-mount/immich/postgres
DB_PASSWORD=<strong-unique-password>
IMMICH_VERSION=v1.70.0  # Pin to tested version
TZ=America/New_York  # Your timezone
```

## Security Checklist

### Secrets Management
- [ ] `.env` file is in `.gitignore` (never commit secrets)
- [ ] `DB_PASSWORD` is strong and unique (minimum 16 characters for production)
- [ ] Only alphanumeric characters in `DB_PASSWORD` (no special chars)
- [ ] `.env.example` created as template (with dummy values) for team reference
- [ ] Secrets stored in secure location (password manager, secrets service)

### Access Control
- [ ] `.env` file permissions: `600` (readable/writable only by owner)
- [ ] `UPLOAD_LOCATION` has appropriate permissions for Docker
- [ ] `DB_DATA_LOCATION` has appropriate permissions for PostgreSQL container
- [ ] Only authorized personnel have `.env` file access in production

### Backups & Recovery
- [ ] Regular backups of both `UPLOAD_LOCATION` and `DB_DATA_LOCATION`
- [ ] `.env` values documented in secure password manager
- [ ] Recovery procedure tested before production deployment
- [ ] `DB_PASSWORD` stored separately from `.env` file

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `env_file not loading` | Verify `.env` exists in compose directory; check syntax (no extra spaces) |
| `DB_PASSWORD` with special chars fails | Use only `A-Za-z0-9`; regenerate if needed |
| `UPLOAD_LOCATION` permission denied | Check permissions: `chmod 755 <path>` and container user has read/write |
| `DB_DATA_LOCATION` on network mount fails | Move to local SSD; network mounts don't work with PostgreSQL |
| Container won't start | Run `docker-compose config` to check for undefined vars; should show resolved values |
| Immich version won't update | Pull latest image: `docker-compose pull immich-server immich-machine-learning` |

## Verification Commands

### Validate .env is loaded
```bash
docker-compose config | grep -A 5 'environment'
```

### Check container environment
```bash
docker exec immich_server env | grep UPLOAD_LOCATION
docker exec immich_postgres env | grep DB_PASSWORD
```

### Verify storage paths exist and are writable
```bash
ls -la $(grep UPLOAD_LOCATION .env | cut -d= -f2)
ls -la $(grep DB_DATA_LOCATION .env | cut -d= -f2)
```

## Best Practices Summary

1. **Never commit `.env` to version control** — Use `.env.example` for templates
2. **Change DB_PASSWORD in production** — Default `postgres` is security risk
3. **Pin IMMICH_VERSION for stability** — Test upgrades in staging first
4. **Use fast SSD storage for DB_DATA_LOCATION** — Performance-critical
5. **Regular backups** — Back up both storage paths before updates
6. **Environment parity** — Keep staging as close to production as possible
7. **Document custom settings** — Comment any modifications for team reference
8. **Secrets rotation** — Update DB_PASSWORD quarterly in production

---

**Official Reference**: https://immich.app/docs/install/environment-variables
**Last Updated**: 2026-05-14

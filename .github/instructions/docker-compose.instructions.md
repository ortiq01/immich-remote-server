---
name: Docker Compose Configuration Guidelines
description: "Use when: editing docker-compose.yml files for Immich media server. Provides best practices for service configuration, volume management, networking, and environment handling."
applyTo: "docker-compose.yml*"
---

# Docker Compose Configuration Guidelines for Immich

## Service Dependencies & Order

Services must maintain proper dependency chains:
```
immich-server → redis (cache layer)
            → database (PostgreSQL)

immich-machine-learning → (independent but benefits from redis)
```

Always verify `depends_on` clauses reflect this order. Ensure `depends_on` includes both `redis` and `database` for `immich-server`.

## Volume Management

### Named Volumes (for data persistence)
- `model-cache`: Stores ML models—DO NOT DELETE without backup
- Always use named volumes for databases and caches to ensure data survives container restarts

### Bind Mounts (for local filesystem access)
- **UPLOAD_LOCATION** (`${UPLOAD_LOCATION}:/usr/src/app/upload`): User media storage
  - Controlled by `.env` file, not hardcoded
  - Should point to high-capacity, fast storage (SSD preferred)
  
- **DB_DATA_LOCATION** (`${DB_DATA_LOCATION}:/var/lib/postgresql/data`): Database storage
  - Critical for performance; MUST be on SSD
  - NO network shares allowed for PostgreSQL
  - Controlled by `.env` file

- **Read-only mounts**:
  - `/shared/nextcloud-photos:/usr/src/app/external/nextcloud:ro` — Nextcloud integration (read-only)
  - `/etc/localtime:/etc/localtime:ro` — Container timezone sync

### Volume Configuration Best Practices
- Use environment variables via `${VAR_NAME}` for path configuration
- Never hardcode absolute paths directly in compose file
- Always include `:ro` suffix for read-only external storage
- Document special mounts with comments

## Port Configuration

- **immich-server**: `2283:2283` — Only externally exposed service
- **redis, database**: No exposed ports (internal only)
- **immich-machine-learning**: No exposed ports (accessed via server)

Do not expose internal services unnecessarily. Add comments if custom ports are needed.

## Environment Configuration

### Using .env File
```yaml
env_file:
  - .env
```

All services should reference `.env` for configuration. Do not hardcode secrets or paths.

### Critical Variables
- `IMMICH_VERSION`: Use version tags (e.g., `release`, `v1.71.0`) not latest
- `DB_PASSWORD`: Change from default `postgres` in production
- `DB_USERNAME`: Usually `postgres` (leave default)
- `DB_DATABASE_NAME`: Usually `immich` (leave default)

## Health Checks

Both Immich services include health checks—keep them enabled for production:

```yaml
healthcheck:
  disable: false
```

For database and cache:
- PostgreSQL: Uses default TCP health check (port 5432)
- Valkey/Redis: Uses `redis-cli ping || exit 1` probe

## Container Restart Policy

```yaml
restart: always
```

All services use `always` restart policy for reliability. Do not change to `unless-stopped` or `no` without strong justification.

## Hardware Acceleration (ML Service)

Optional acceleration for `immich-machine-learning`:

```yaml
extends:
  file: hwaccel.ml.yml
  service: cuda  # Options: armnn, cuda, rocm, openvino, openvino-wsl, rknn
```

When enabled:
- Ensure hardware is available (GPU, NPU, etc.)
- Reference correct `hwaccel.ml.yml` file
- Update image tag to match acceleration type (e.g., `-cuda`)

## Common Modifications

### Adding a New Service
- Add to `services` section
- Include `container_name` for easier management
- Add `env_file: - .env` unless service-specific
- Include `restart: always`
- Add `depends_on` if it relies on redis/database

### Changing Storage Paths
- Never edit mount paths directly in compose file
- Update `.env` file instead: `UPLOAD_LOCATION=` or `DB_DATA_LOCATION=`
- Always restart services after changing paths: `docker-compose down && docker-compose up -d`

### Enabling ML Acceleration
- Uncomment `extends` section in `immich-machine-learning`
- Select appropriate hardware type
- Ensure `hwaccel.ml.yml` exists in same directory
- Update image tag if needed (e.g., `${IMMICH_VERSION:-release}-cuda`)

## Security Checklist

- [ ] `DB_PASSWORD` changed from default
- [ ] Sensitive paths are environment variables, not hardcoded
- [ ] No exposed ports except `2283`
- [ ] Database storage on local SSD (no network mounts)
- [ ] Health checks enabled on all services
- [ ] `.env` file excluded from version control (.gitignore)

## Validation

Before deploying changes:
1. Validate syntax: `docker-compose config` (shows resolved compose file)
2. Check for undefined variables: Look for `null` or `${VAR}` in output
3. Test with dry-run: `docker-compose up --dry-run`
4. Verify volumes exist or will be created
5. Check port conflicts: No service should claim port 2283 except immich-server

## Common Issues

| Issue | Solution |
|-------|----------|
| Container won't start | Check `docker-compose logs <service>` for error |
| Database connection fails | Verify `DB_PASSWORD` matches in both `.env` and container startup |
| ML service crashes | Enable hardware acceleration only if hardware present |
| Storage permission denied | Ensure `UPLOAD_LOCATION` and `DB_DATA_LOCATION` paths exist and are writable |
| `env_file` not loading | Verify `.env` file exists and is in same directory as compose file |
| Port 2283 already in use | Change first port in `ports: ['2283:2283']` to available port |

---

**Reference**: https://immich.app/docs/install/docker-compose

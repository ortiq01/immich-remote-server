---
name: Immich Media Server Setup Guide
description: "Project context for Immich media server with Docker Compose. Provides guidance on Docker services, PostgreSQL, Redis caching, and ML integration for photo/video management."
---

# Immich Media Server - AI Agent Support

You are assisting with the **Immich Media Server** project—a self-hosted photo and video management system supporting multiple media storage environments.

## Project Overview

Immich is a distributed media management platform that:
- Centrally hosts and manages photos and videos from multiple storage sources
- Provides machine learning capabilities for image recognition and organization
- Integrates with external storage systems (Nextcloud, local storage)
- Uses Docker Compose for containerized deployment

## Architecture & Services

### Core Services

**immich-server** (port 2283)
- Main application server handling API requests and user interactions
- Image: `ghcr.io/immich-app/immich-server`
- Depends on: Redis, PostgreSQL
- Mounts media from `UPLOAD_LOCATION` (default: `/rpool/data/immich/library`)
- Integrates read-only Nextcloud storage at `/shared/nextcloud-photos`

**immich-machine-learning**
- Machine learning engine for image recognition, object detection, and video analysis
- Image: `ghcr.io/immich-app/immich-machine-learning`
- Supports hardware acceleration: CUDA, ROCm, OpenVINO, RKNN, ARMnn
- Model cache stored in Docker volume `model-cache`

### Data Layer

**PostgreSQL (Custom Immich Build)**
- Version: 14 with VectorChord (0.3.0) and pgvectors (0.2.0) extensions
- Purpose: Stores metadata, user accounts, and vector embeddings for ML searches
- Data location: `DB_DATA_LOCATION` (default: `/rpool/data/immich/postgres`)
- Credentials managed via `.env` file (`DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE_NAME`)

**Valkey/Redis 8**
- In-memory caching and session management
- Improves API performance and real-time updates
- Health check: Redis ping probe

### Storage

- **Media Storage**: Configurable via `UPLOAD_LOCATION` environment variable
- **Database Storage**: Configurable via `DB_DATA_LOCATION` (SSDs recommended; HDD support available)
- **Model Cache**: Docker volume for ML models persistence

## Configuration

### Environment Variables (.env)
```
UPLOAD_LOCATION=/rpool/data/immich/library
DB_DATA_LOCATION=/rpool/data/immich/postgres
IMMICH_VERSION=release  # Pin to specific version if needed (e.g., v1.71.0)
DB_USERNAME=postgres
DB_PASSWORD=<change-this>
DB_DATABASE_NAME=immich
TZ=Etc/UTC  # Optional timezone
```

### Hardware Acceleration
ML acceleration can be enabled by uncommenting the `extends` section in the compose file and selecting:
- `-cuda` for NVIDIA GPUs
- `-rocm` for AMD GPUs
- `-openvino` for Intel CPUs
- `-rknn` for Rockchip
- `-armnn` for ARM devices

## Common Tasks

### When Making Changes
- **Docker Compose updates**: Ensure `depends_on` order is preserved (server → redis/database)
- **Volume management**: Use named volumes (`model-cache`) for data persistence; update paths in `.env`
- **Health checks**: Both immich services have health checks enabled; keep them enabled
- **Environment variables**: Only modify via `.env`; never hardcode secrets

### Database Operations
- PostgreSQL includes VectorChord for advanced vector search
- pgvectors extension enables ML embedding storage and similarity search
- Custom docker image: `ghcr.io/immich-app/postgres:14-vectorchord0.3.0-pgvectors0.2.0`

### Nextcloud Integration
- Read-only mount at `/shared/nextcloud-photos`
- Allows Immich to ingest photos from Nextcloud without duplication
- Modify mount path in server volumes section if Nextcloud storage location changes

## Key Guidelines

1. **Always check official docs**: https://immich.app/docs/install/environment-variables
2. **Version pinning**: Use specific `IMMICH_VERSION` in production to avoid unexpected changes
3. **Database backups**: Back up PostgreSQL data regularly from `DB_DATA_LOCATION`
4. **Storage planning**: Immich serves as centralized hub; ensure adequate storage for all media sources
5. **Network shares**: PostgreSQL **does not support** network shares for database storage
6. **Container restart policy**: Set to `always` for production reliability

## Support & Learning Resources

- **Official Documentation**: https://immich.app/docs
- **GitHub Repository**: https://github.com/immich-app/immich
- **Docker Compose Release**: https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml
- **Hardware Acceleration**: https://immich.app/docs/features/ml-hardware-acceleration

## Agent Capabilities for This Project

When assisting with this repository, I can help with:
- ✅ Docker Compose configuration and troubleshooting
- ✅ Environment variable optimization and security
- ✅ Service dependency management
- ✅ Volume and storage configuration
- ✅ Database schema and performance tuning
- ✅ ML acceleration setup and hardware compatibility
- ✅ Nextcloud integration configuration
- ✅ Security best practices (password rotation, secrets management)
- ✅ Health check configuration and monitoring
- ✅ Multi-environment setup (dev, staging, production)

---

**Last Updated**: 2026-05-14
**Project**: Immich Media Server (Docker Compose)

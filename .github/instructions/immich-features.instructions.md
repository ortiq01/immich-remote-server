---
name: Immich Application Features & Capabilities
description: "Use when: working with Immich application logic, features, or functionality. Provides guidance on ML features, search, libraries, sharing, users, and advanced capabilities beyond infrastructure setup."
applyTo: "**/*"
---

# Immich Application Features & Capabilities

## Application Overview

Immich is a **self-hosted photo & video management platform** with AI-powered organization, intelligent search, and collaborative features. It's designed as an alternative to cloud-based services like Google Photos or Amazon Photos, giving users complete control over their media.

### Core Philosophy
- **Privacy-First**: All data stays on your infrastructure; no cloud dependency
- **Multi-Source**: Ingest media from multiple storage systems (Nextcloud, local storage, mobile uploads)
- **AI-Powered**: ML features for tagging, recognition, and intelligent search
- **Collaborative**: Multi-user support with granular permissions

## Core Features

### 1. Library Management

**Asset Organization**
- Centralized library for all photos and videos from multiple sources
- Automatic deduplication to prevent duplicate media
- Metadata preservation (EXIF, creation date, camera info)
- Support for extensive media formats (JPEG, PNG, RAW, HEIC, MP4, MOV, WebP, etc.)
- Directory-based organization or flat library with AI tagging

**Smart Import**
- Auto-import from watched directories
- Nextcloud integration for seamless photo library syncing
- Mobile app for direct uploads
- Bulk upload from web interface
- Archive/unarchive capability

### 2. Machine Learning Features

**Image Recognition** (Powered by ML model)
- Automatic object detection (cat, dog, car, building, etc.)
- Scene detection (outdoor, indoor, beach, mountain, etc.)
- Activity recognition (running, walking, sports, etc.)
- Quality assessment (blurry detection, exposure analysis)

**Face Recognition** (Optional, requires face DB setup)
- Automatic face detection in photos
- Face clustering for identifying recurring people
- Face search and grouping
- Privacy-respecting on-device processing (no cloud)

**Smart Search**
- Content-based search using ML embeddings
- Natural language search ("photos of my dog at the beach")
- Similar image search
- Advanced filters by date, camera, location, etc.

**Album Suggestions**
- Automatic album creation based on date/location
- Smart grouping by event or trip
- ML-driven album recommendations

### 3. Search & Organization

**Advanced Search Filters**
- Date range filtering (calendar picker)
- Camera/lens information
- Location-based search (with map integration)
- Media type (photos only, videos only, burst photos, etc.)
- Exposure/quality filters
- Person/face search

**Collections & Albums**
- User-created albums for custom grouping
- Collaborative albums (invite others)
- Smart albums with auto-population rules
- Album sharing with view-only or edit permissions
- Timeline view of albums

**Tags & Metadata**
- Manual tagging (user-applied keywords)
- Auto-tagging from ML models
- Custom tag hierarchies
- Tag-based search and filtering
- Metadata editing (title, description, date)

### 4. Sharing & Collaboration

**Sharing Options**
- Share individual photos with secure links
- Share albums with expiring links
- Password-protected sharing
- Download restrictions (view-only vs. downloadable)
- Share with specific users in multi-user setup

**Multi-User Support**
- User accounts with authentication
- Role-based access control (Admin, User, etc.)
- Private vs. shared libraries
- User-specific preferences and settings
- Activity logs

**Collaborative Features**
- Shared albums for family/team collaboration
- Comments on photos (planned feature)
- Edit permissions for shared content
- Photo contributions to collaborative albums

### 5. Media Viewing & Playback

**Photo Viewing**
- Full-screen lightbox with controls
- Slideshow mode with adjustable timing
- Zoom and pan functionality
- Metadata sidebar (EXIF, camera info, location)
- Map view showing photo locations

**Video Playback**
- Native video player with playback controls
- Video transcoding for compatibility
- Thumbnail preview generation
- Duration and codec information
- Adaptive bitrate streaming (if enabled)

**Batch Operations**
- Select multiple photos
- Batch tagging
- Batch deletion
- Batch download as ZIP
- Move to archive/trash

### 6. Advanced Features

**Timeline View**
- Chronological display of all media
- Jump to specific dates/years
- Collapsible date groupings
- Visual scroll timeline

**Map Integration**
- Show photos on world map (if GPS data available)
- Cluster view for location-heavy areas
- Filter by geographic region
- Location-based album suggestions

**Memories/Recall**
- "On this day" feature showing photos from years past
- Automatic memory creation for anniversaries
- Random photo suggestions
- Timehop-style reminders

**Trash/Archive**
- Soft delete with recovery window (30 days default)
- Archive photos/videos without deleting
- Permanent deletion option
- Archive-only view

### 7. Mobile Apps

**Features**
- Full library access on mobile
- Photo/video upload directly from phone
- Offline viewing (cached content)
- Live photo support (iPhone HEIC with motion)
- Background sync
- Push notifications for shared albums

**Platforms**
- iOS (AppStore)
- Android (Google Play, F-Droid)
- Web interface (responsive design)

## Search Capabilities

### Search Types

| Type | Example | Use Case |
|------|---------|----------|
| **ML Object Search** | "photos with dogs" | Find by detected objects |
| **Text Search** | "vacation 2024" | Search tags and metadata |
| **Similar Image** | Click image → "Find Similar" | Duplicates or style matching |
| **Advanced Filters** | Date + Camera + Location | Precise multi-criteria search |
| **Person Search** | "photos of John" | Face recognition results |
| **Location Search** | "San Francisco" | Geolocation-based |

### Smart Search Engine
- Vector embeddings for semantic search
- PostgreSQL with pgvectors extension enables similarity queries
- Fast indexed searches for text fields
- Faceted search (filter by multiple criteria simultaneously)

## User Roles & Permissions

### Admin User
- Full system access
- User management
- System settings configuration
- Library administration

### Regular User
- Access to own library
- Can create private albums
- Can accept shared album invitations
- Limited to personal settings

### Shared Album Access
- View-only mode (cannot delete/edit)
- Edit mode (can add/remove/organize photos)
- Download permissions controlled separately

## Database Schema Highlights

The PostgreSQL database (with VectorChord and pgvectors) stores:

### Core Tables
- **assets**: Photo/video files with metadata
- **users**: User accounts and credentials
- **albums**: Album definitions and compositions
- **asset_faces**: Face detection and clustering results
- **smart_search**: ML embeddings for semantic search
- **shared_links**: Sharing tokens and permissions
- **tags**: Custom tags and taxonomy
- **libraries**: Multi-library support

### Vector Embeddings
- ML model outputs stored as vectors (pgvectors)
- Enables similarity search ("find photos similar to this")
- Powers smart recommendations
- Semantic search across image content

## API Access

### REST API
- Photo CRUD operations
- Album management
- User/auth endpoints
- Search and filtering
- Asset metadata updates

### GraphQL (Beta)
- Query-optimized access
- Real-time subscriptions
- Complex multi-relation queries

### API Keys
- Personal API keys for automation
- Read-only or full-access scopes
- Programmatic album creation
- Webhook support (planned)

## Performance Considerations

### Indexing
- PostgreSQL full-text search indexes for fast text queries
- Vector indexes for semantic search
- Date/camera/location indexes for common filters

### Caching
- Redis caches frequently accessed data
- Asset metadata caching
- Search result caching
- Session management

### Image Processing
- Thumbnail generation on upload
- Progressive image serving
- Adaptive video bitrate streaming
- On-demand transcoding

## Configuration & Customization

### Application Settings
- Thumbnail sizes
- Video transcoding profiles
- ML model selection
- Search behavior tuning
- Trash retention period (default 30 days)

### Theme & UI
- Dark/light mode
- Custom appearance settings
- Language support
- Interface density settings

### Advanced Options
- Custom storage paths
- External reverse proxy setup
- SSL/TLS configuration
- Rate limiting
- CORS and security headers

## Common Workflows

### Organize New Media
1. Upload photos via web/mobile/auto-import
2. Immich auto-tags with ML models
3. Review and refine tags
4. Create album (automatic or manual)
5. Optional: Invite collaborators

### Search & Retrieve
1. Use smart search ("mountain landscape")
2. Apply filters (date range, camera, quality)
3. Browse results with timeline
4. Create collection from results
5. Share selected photos

### Share with Family
1. Create collaborative album
2. Set permissions (view/edit/download)
3. Generate share link or invite users
4. Family members add photos to album
5. Receive notifications on contributions

### Archive Old Media
1. Apply filters (before specific date)
2. Select batch results
3. Archive instead of delete
4. Archive stays searchable but hidden from main timeline
5. Recover later if needed

## Integration Points

### Nextcloud
- Read-only sync of Nextcloud Photos folder
- Keep Immich library in sync with Nextcloud
- Duplicate prevention

### Mobile Devices
- iOS/Android native apps
- WiFi-triggered auto-sync
- Selective folder backup

### External Tools
- REST API for custom automation
- Webhook notifications (when available)
- EXIF data preservation and editing

## Data Organization Best Practices

### By Date
- Year-based folders
- Month/week groupings
- Timeline view for chronological access

### By Event
- Create albums for vacations, weddings, etc.
- AI-assisted event detection
- Date-based auto-grouping

### By Person
- Face recognition for recurring people
- Smart collections of specific people
- Private person libraries

### By Location
- Geographic tagging
- Map-based organization
- Location-based search filters

## Limitations & Considerations

- **Network Share DB**: PostgreSQL doesn't support network-mounted database storage (requires local SSD)
- **Large Libraries**: Performance scales well but extremely large collections (1M+ photos) benefit from index optimization
- **Face Recognition**: Requires significant compute; can be disabled if not needed
- **Raw Photo Support**: Requires transcoding; RAW files not shown in timeline without conversion
- **Live Photos**: Full support on iOS; Android support depends on format

## Learning Resources

- **Official Docs**: https://immich.app/docs
- **Feature Roadmap**: https://github.com/immich-app/immich/discussions
- **Community Wiki**: https://immich.app/docs/community-wiki
- **GitHub Discussions**: Active community for tips and workflows

---

**Last Updated**: 2026-05-14

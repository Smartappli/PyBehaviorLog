# Changelog

## 0.9.5

- Unified export schema/version markers to 0.9.5 across session JSON, bundle manifest, compatibility report, SQL header and CowLog header.
- Preserved backward import compatibility for 0.9.1 schemas while adding acceptance for 0.9.5 schemas.
- Carried forward v0.9.3 review queue filtering/export consistency and batch assignment behavior.
- Added BORIS 9.12.1 compatibility coverage for native `.boris` project JSON imports, BORIS tabular preambles, TextGrid point tiers, aggregated event TSV exports, and FERAL JSON exports.
- Added native `.boris` export profiles for BORIS 7, BORIS 8, and BORIS 9 on project and session export screens.
- Added a BORIS 9.x-style tabular events TSV export with observation metadata, variables, modifiers, event status, media name, and frame index fields.
- Hardened native `.boris` imports for BORIS image-observation event rows and modifier values containing shortcut suffixes, spacing, or `None` placeholders.
- Added native `.boris` `IMAGES` observation export for image-only sessions, including image directories, image indexes, and image paths.
- Added native `.boris` `media_info.frames` output when FPS and media duration are available.

## 0.9.4

- Restored Django runtime target to 6.0.3.
- Audited and stabilized review queue/export behavior and batch segment assignment paths.
- Hardened production security defaults (non-default `DJANGO_SECRET_KEY`, required `ALLOWED_HOSTS`, optional TLS/HSTS controls).
- Updated dependency constraints to newer maintained versions (Django, Granian, Argon2, psycopg, redis, Ruff).
- Kept Granian as the default ASGI runtime across docs and metadata.

## 0.9.3

- Refined review queue filtering logic into a shared helper for maintainability.
- Aligned review-segment CSV export with active queue filters used in the UI.
- Bumped release metadata and docs to 0.9.3.
- Documented Granian as the default ASGI command for local startup parity.

## 0.9.2

- Added batch assignment for review segments directly from the session player.
- Added finer review queue filters (project, status, assignee, reviewer, and text search).
- Added CSV analytics export for review segments from the review queue.

## 0.9.1

- Added segment-level review queues and session review segments.
- Added review queue dashboard and session-level segment CRUD screens.
- Included review segments in 0.9.1 session exports/imports and project cloning.

## 0.9

- Added import-as-new-project workflow from BORIS project JSON or PyBehaviorLog bundle ZIP/JSON.
- Added project cloning with optional session and video metadata duplication.
- Added `/health/` and `/release.json` operational endpoints.
- Added management commands for release metadata and project bundle export.
- Added Docker health checks for the ASGI service.

## 0.8.9

- Added server-side undo/redo for event operations.
- Expanded BORIS-like tabular imports and picture sequence handling.

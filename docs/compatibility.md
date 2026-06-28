# Compatibility profile for PyBehaviorLog 0.9.1

PyBehaviorLog 0.9.1 strengthens interoperability with BORIS and CowLog around the formats and workflows that are publicly documented.

## BORIS coverage

### BORIS 9.12.1 compatibility additions

- Native `.boris` project JSON files are detected by BORIS signatures such as `project_format_version`, `subjects_conf`, and `behaviors_conf`, then normalized into the PyBehaviorLog import profile.
- Project and session screens expose native `.boris` exports for BORIS 7, BORIS 8, and BORIS 9 profiles. BORIS 9.12.1 still declares native project files with `project_format_version` set to `7.0`; PyBehaviorLog keeps that value and varies optional observation/media fields by profile.
- BORIS tabular CSV/TSV/XLSX imports now tolerate metadata preambles before the event header and accept recent aliases such as `Start (s)`, `Stop (s)`, `Duration (s)`, and `FPS (frame/s)`.
- Session exports include a BORIS 9.x-style tabular events TSV with observation metadata, media duration/FPS fields, independent variables, modifiers, event status, media file name, and frame index.
- TextGrid exports now emit point events as `TextTier` tiers and split overlapping state intervals into separate subject/behavior tiers.
- Session exports include a BORIS-style aggregated events TSV with `Media duration (s)` and `FPS (frame/s)` columns for BORIS 9.x analysis plugins.
- Session exports include a FERAL-compatible JSON label payload modeled on the BORIS FERAL export plugin.
- Native `.boris` imports normalize BORIS image-observation event rows by preserving the image index as PyBehaviorLog `frame_index` and keeping the image path as event context when no explicit comment is present.
- Native `.boris` imports trim modifier values with BORIS shortcut suffixes such as `fast (f)` and ignore `None` placeholder modifier tokens.

### Implemented in 0.9

- BORIS-compatible observation JSON export
- BORIS-compatible project JSON export
- Native `.boris` project/session export profiles for BORIS 7, BORIS 8, and BORIS 9
- BORIS-style tabular events TSV export
- Project import from BORIS-like project JSON payloads using both list and mapping shapes
- Observation import from BORIS-like observation JSON payloads
- Behavioral sequence export
- Praat TextGrid export
- Binary table export
- CSV, TSV, JSON, XLSX tabular exports
- Transition summaries and interval analytics inside PyBehaviorLog exports

### Current positioning

This is a **strong compatibility layer**, but not a formal certification against every historical BORIS project file ever produced.

The safest paths are:

- BORIS JSON project/observation workflows documented in the BORIS user guide
- BORIS-style tabular exports
- Structured round-trips through PyBehaviorLog reproducibility bundles

## CowLog coverage

### Implemented in 0.9

- Import of documented CowLog-like plain-text coding result files
- Export of CowLog-compatible plain-text result files
- Mapping through behavior names and keyboard shortcuts
- Modifier-aware import/export for plain-text rows

### Current positioning

CowLog compatibility in 0.9 focuses on the **documented plain-text coding result workflow**.

CowLog plain-text exports do not preserve all PyBehaviorLog/BORIS semantics with the same fidelity, especially for:

- paired state events
- annotations
- richer review/audit metadata
- observation variables

For those cases, BORIS JSON and PyBehaviorLog JSON remain the preferred interchange formats.


## CowCloud coverage

CowCloud is not currently certified or implemented as an exchange target.

The repository does not include a CowCloud API contract, SDK reference, file
format sample, or representative export corpus. Compatibility reports therefore
mark CowCloud as `blocked_pending_format_contract`.

Before implementing this adapter, collect the CowCloud contract described in
`docs/compatibility_matrix.md`: authentication, project/session/animal schema,
event timestamp rules, point/state behavior semantics, media handling, biometric
field mappings, and representative gold files.


## Built-in certification baseline

Version 0.9 adds a compact fixture corpus and automated round-trip tests for:

- BORIS observation JSON
- BORIS project JSON
- CowLog-compatible plain-text result files

Those fixtures are executed in the Django test suite and compared through normalization helpers so CI can detect semantic regressions even when raw JSON shapes differ.

## Compatibility reports

PyBehaviorLog 0.9.1 adds machine-readable compatibility reports at both project and session level.

They summarize:

- detected or targeted exchange family
- documented import/export families
- readiness warnings
- feature mismatches that may reduce fidelity

## Recommended certification workflow

If you want to move toward a stronger "certified compatibility" claim, use this workflow:

1. Build a gold corpus of BORIS and CowLog reference files.
2. Import them into PyBehaviorLog.
3. Export them back out.
4. Re-import the exported files.
5. Compare events, subjects, modifiers, variables, and timing programmatically.
6. Store the round-trip reports in CI.

That approach is the right path toward a future compatibility certification release.

See `docs/compatibility_matrix.md` for the current per-application matrix and
the CowCloud contract checklist.


### Added in 0.9

- BORIS-style tabular session imports from CSV, TSV, and XLSX files
- relative media paths included in project/session JSON payloads and reproducibility bundles
- lightweight media diagnostics for compatible local audio files, including waveform previews and a coarse spectrogram
- additional HTML and SQL exports for review and downstream analysis pipelines


## Additional notes for 0.9

Version 0.9 extends the compatibility and review toolchain with server-side undo/redo for event operations, broader BORIS-style spreadsheet imports, and richer handling of picture-based media paths and image sequences.


## Operational additions in 0.9

Version 0.9 adds a project lifecycle layer on top of the existing compatibility tooling:

- project import as a **new project** from BORIS project JSON or PyBehaviorLog bundles
- project cloning for parallel review, training, or branching workflows
- deployment-oriented `/health/` and `/release.json` endpoints
- management commands for bundle export and release reporting

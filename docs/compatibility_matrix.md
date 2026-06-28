# Compatibility matrix

This matrix separates implemented exchange paths from paths that still require
an external contract or a larger certification corpus.

## Status legend

- **Implemented**: code path exists and is covered by local tests or fixtures.
- **Certified baseline**: covered by the built-in round-trip fixture corpus.
- **Compatible profile**: PyBehaviorLog emits or accepts a documented adjacent
  format, but this is not a guarantee that the third-party application accepts
  every payload as native.
- **Blocked**: no public format/API contract is available in this repository.

## BORIS

| Capability | Current status | Implementation | Main residual risk |
| --- | --- | --- | --- |
| Project JSON import/export | Certified baseline | `build_project_boris_payload`, `import_project_payload` | `boris-project-v*` is accepted by regex, so future schema drift must be tested with real files. |
| Native `.boris` project import | Implemented | `normalize_native_boris_project_payload`, `import_project_payload` | Native BORIS files without `schema` are normalized from `project_format_version`, `subjects_conf`, `behaviors_conf`, and `observations`; unusual future event-list layouts still need gold files. |
| Native `.boris` project/session export | Compatible profile | `build_native_boris_project_payload`, `project_export_boris_native`, `session_export_boris_native` | BORIS 9.12.1 still writes `project_format_version` as `7.0`; export profiles target BORIS 7/8/9 by adjusting optional media and observation fields, including BORIS 8/9 `observation time interval`, `media_info.frames`, BORIS 9 `media_info.display`, and BORIS 9 media playback defaults when applicable. |
| Observation JSON import/export | Certified baseline | `build_boris_like_payload`, `import_session_payload` | Export is BORIS-compatible, not a formal native `.boris` writer. |
| CSV/TSV/XLSX event import | Implemented | `parse_tabular_session_rows` | Header aliases include BORIS 9.x `Start (s)`, `Stop (s)`, `Duration (s)`, `FPS (frame/s)`, and metadata preambles; real exports can still contain unsupported columns. |
| Tabular events TSV export | Compatible profile | `build_boris_tabular_event_rows` | Mirrors BORIS 9.x event-row columns; media file attribution is based on stored PyBehaviorLog media links. |
| Behavioral sequences | Compatible profile | `build_behavioral_sequences_text` | Intended for downstream sequence tools, not lossless project exchange. |
| Praat TextGrid | Compatible profile | `build_textgrid_text` | Point events are exported as `TextTier`; full ethogram/project metadata still belongs in JSON. |
| Binary table | Compatible profile | `build_binary_table_rows` | Sampling step can change analytical interpretation. |
| Aggregated events TSV | Compatible profile | `build_boris_aggregated_event_rows` | Exposes BORIS 9.x plugin columns including media duration and FPS; values depend on stored variables or available media diagnostics. |
| FERAL JSON | Compatible profile | `build_feral_payload` | Requires FPS and duration to generate frame labels; overlapping behaviors are reported in warnings. |
| Picture/live observations | Partial | native image event indexes, image paths, media paths, frame indices | Native BORIS image observations are imported as PyBehaviorLog media sessions with directory paths retained; image-only PyBehaviorLog sessions export as BORIS `IMAGES`; a larger gold corpus is still needed for certification. |

## CowLog

| Capability | Current status | Implementation | Main residual risk |
| --- | --- | --- | --- |
| Plain-text result import | Certified baseline | `parse_cowlog_results_text` | Unknown behavior tokens are skipped unless strict mode is used. |
| Plain-text result export | Implemented | `session_export_cowlog_txt` | State pairing, annotations, and variables are not fully lossless in CowLog text. |
| FPS/timecode handling | Implemented | `_decimal`, CowLog metadata parsing | Timecode interpretation depends on valid `fps` metadata. |
| Modifier and subject mapping | Implemented | token lookup maps | Ambiguous free-text tokens can be misclassified as subjects. |

## CowCloud

| Capability | Current status | Implementation | Main residual risk |
| --- | --- | --- | --- |
| Data import/export | Blocked | none yet | No public CowCloud schema/API sample is available in the repository. |
| SDK integration | Prepared | `tracker.dealhost`-style lazy SDK boundary should be mirrored once CowCloud SDK details exist | The SDK package name, auth model, and endpoint model are unknown. |
| Certification | Blocked | compatibility reports expose `blocked_pending_format_contract` | Requires real CowCloud exports or API contract. |

## Required CowCloud contract

Before claiming CowCloud compatibility, collect:

1. SDK package name and supported Python versions.
2. Authentication flow and secret names.
3. Project/session/animal schema.
4. Event timestamp units, timezone rules, and frame-rate handling.
5. Point/state behavior semantics.
6. Modifier, annotation, media, and biometric field mappings.
7. At least three representative export files or API snapshots for CI fixtures.

## Certification expansion

Add gold files under `tracker/tests/fixtures/` and validate each family through:

1. Import source file.
2. Persist to the Django model.
3. Export through the target profile.
4. Re-import the export.
5. Compare normalized events, subjects, modifiers, variables, annotations, media paths, and timings.

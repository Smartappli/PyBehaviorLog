# Native BORIS `.boris` Profile Matrix

This matrix tracks the native `.boris` project shape emitted or accepted by
PyBehaviorLog for BORIS 7, BORIS 8, and BORIS 9. It is based on BORIS 9.12.1
source inspection plus historical tag checks for fields that are profile
specific.

BORIS 9.12.1 still stores native project files with
`project_format_version: "7.0"`. PyBehaviorLog therefore keeps that value for
all native export profiles and varies optional fields by target profile.

## Project Keys

| Key | Import | BORIS 7 export | BORIS 8 export | BORIS 9 export | Notes |
| --- | --- | --- | --- | --- | --- |
| `time_format` | Accepted | Yes | Yes | Yes | Exported as `hh:mm:ss`. |
| `project_name` | Accepted | Yes | Yes | Yes | From `Project.name`. |
| `project_date` | Accepted | Yes | Yes | Yes | ISO timestamp. |
| `project_description` | Accepted | Yes | Yes | Yes | From `Project.description`. |
| `project_format_version` | Detection key | `7.0` | `7.0` | `7.0` | Matches BORIS 9.12.1 native writer. |
| `subjects_conf` | Accepted | Yes | Yes | Yes | Mapping shape normalized on import. |
| `behaviors_conf` | Accepted | Yes | Yes | Yes | Mapping shape normalized on import. |
| `observations` | Accepted | Yes | Yes | Yes | Mapping by observation id/title. |
| `behavioral_categories` | Accepted | Yes | Yes | Yes | Ordered names. |
| `behavioral_categories_config` | Accepted | No | No | Yes | Preserves BORIS 9 category colors. |
| `independent_variables` | Accepted | Yes | Yes | Yes | Exported from project variable definitions. |
| `coding_map` | Preserved as empty adapter field | Yes | Yes | Yes | PyBehaviorLog does not author BORIS coding maps. |
| `behaviors_coding_map` | Preserved as empty adapter field | Yes | Yes | Yes | PyBehaviorLog does not author BORIS behavior coding maps. |
| `converters` | Preserved as empty adapter field | Yes | Yes | Yes | PyBehaviorLog does not author BORIS external-data converters. |

## Observation Keys

| Key | Import | BORIS 7 export | BORIS 8 export | BORIS 9 export | Notes |
| --- | --- | --- | --- | --- | --- |
| `date` | Accepted | Yes | Yes | Yes | ISO timestamp from session date. |
| `file` | Accepted | Yes | Yes | Yes | `[]` for live, player mapping for media, `{}` for `IMAGES`. |
| `type` | Accepted | Yes | Yes | Yes | `LIVE`, `MEDIA`, or `IMAGES`. |
| `visualize_spectrogram` | Accepted | Yes | Yes | Yes | Exported as `false`. |
| `time offset` | Accepted | Yes | Yes | Yes | Exported as `0.0`. |
| `independent_variables` | Accepted | Yes | Yes | Yes | Per-session variable values. |
| `close_behaviors_between_videos` | Accepted | Yes | Yes | Yes | Exported as `false`. |
| `events` | Accepted | Yes | Yes | Yes | Native event rows. |
| `description` | Accepted | Yes | Yes | Yes | Session description. |
| `media_info` | Accepted | Yes | Yes | Yes | See media-info matrix below. |
| `scan_sampling_time` | Accepted | No | Yes | Yes | Neutral value `0`. |
| `observation time interval` | Accepted | No | Yes | Yes | Neutral value `[0, 0]`; absent from checked BORIS 7 tags. |
| `visualize_waveform` | Accepted | No | No | Yes | Exported as `false`. |
| `start_from_current_time` | Accepted | No | No | Yes | Exported as `false`. |
| `media_creation_date_as_offset` | Accepted | No | No | Yes | BORIS 9 neutral value `false`. |
| `media_scan_sampling_duration` | Accepted | No | No | Yes | BORIS 9 neutral value `0`. |
| `image_display_duration` | Accepted | No | No | Yes | BORIS 9 neutral value `1`. |
| `directories_list` | Accepted | Image sessions only | Image sessions only | Image sessions only | Used for BORIS `IMAGES` observations. |

## `media_info` Keys

| Key | Import | BORIS 7 export | BORIS 8 export | BORIS 9 export | Notes |
| --- | --- | --- | --- | --- | --- |
| `length` | Accepted | Yes | Yes | Yes | Media duration by path when known. |
| `fps` | Accepted | Yes | Yes | Yes | FPS by path when known. |
| `hasVideo` | Accepted | Yes | Yes | Yes | Derived from media extension. |
| `hasAudio` | Accepted | Yes | Yes | Yes | Derived from media extension. |
| `offset` | Accepted | Yes | Yes | Yes | Per-player offset, default `0.0`. |
| `frames` | Accepted | Conditional | Conditional | Conditional | Written when FPS and duration are known. |
| `display` | Accepted | No | No | Yes | BORIS 9 player visualization setting, default `Nothing`. |

## Event Rows

| Event row field | Import | BORIS 7 export | BORIS 8 export | BORIS 9 export | Notes |
| --- | --- | --- | --- | --- | --- |
| time | Accepted | Yes | Yes | Yes | Seconds as float. |
| subject | Accepted | Yes | Yes | Yes | Empty string when no subject is assigned. |
| behavior | Accepted | Yes | Yes | Yes | Behavior name/code. |
| modifiers | Accepted | Yes | Yes | Yes | `|`-joined modifier names on export. |
| comment | Accepted | Yes | Yes | Yes | Event comment. |
| frame index | Accepted | No | Yes | Yes | Added for media events when stored. |
| image index | Accepted | Image events only | Image events only | Image events only | Preserved as PyBehaviorLog `frame_index`. |
| image path | Accepted | Image events only | Image events only | Image events only | Preserved as event context/comment fallback. |

## Import Normalization Coverage

| Native shape | Current behavior |
| --- | --- |
| Mapping-shaped `subjects_conf` and `behaviors_conf` | Normalized into PyBehaviorLog subjects and ethogram rows. |
| `behavioral_categories_config` with hex colors | Preserved as category colors. |
| Modifier values such as `fast (f)` | Shortcut suffix is trimmed. |
| `None` modifier placeholders | Ignored. |
| `IMAGES` event rows | Image index and image path are preserved. |
| Media player mappings | Flattened into ordered media paths. |

## Remaining Certification Gaps

- Add real BORIS-authored gold files for BORIS 7, BORIS 8, and BORIS 9.12.1.
- Validate generated `.boris` files by opening them in BORIS 9.12.1 and checking
  whether BORIS rewrites or warns about any fields.
- Add multi-player media and external data plot fixtures before claiming coverage
  for those BORIS features.

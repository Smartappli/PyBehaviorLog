from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

SESSION_EVENT_SCHEMAS = {
    'cowlog-results-v1',
    'cowlog-results-v2',
    'pybehaviorlog-0.9-session',
    'pybehaviorlog-0.9.1-session',
    'pybehaviorlog-0.8.3-session',
    'pybehaviorlog-0.8-session',
    'boris-tabular-csv-v1',
    'boris-tabular-tsv-v1',
    'boris-tabular-xlsx-v1',
    'boris-tabular-spreadsheet-v2',
}


def _normalize_time(value: Any) -> float:
    try:
        return round(float(Decimal(str(value))), 3)
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


def _unique_sorted_nonempty(items: list[str]) -> list[str]:
    return sorted({item for item in items if item})


def _coerce_named_item(item: Any, fallback: str = '') -> str:
    if isinstance(item, dict):
        return str(item.get('name') or item.get('label') or fallback)
    return str(item)


def _string_list_from_mapping(value: dict[Any, Any]) -> list[str]:
    values = []
    for key, item in value.items():
        if isinstance(item, dict):
            values.append(_coerce_named_item(item, str(key)))
        elif item:
            values.append(str(key))
    return _unique_sorted_nonempty(values)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split('|') if item.strip()]
    if isinstance(value, dict):
        return _string_list_from_mapping(value)
    if isinstance(value, list):
        return _unique_sorted_nonempty([_coerce_named_item(item) for item in value])
    return [str(value)]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, list):
        return value
    return []


def _dict_items(value: Any) -> list[dict[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, dict)]


def _merge_observation_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    merged_items: list[dict[str, Any]] = []
    for observation in _dict_items(payload.get('observations')):
        merged_items.extend(_dict_items(observation.get(key, [])))
    return merged_items


def _resolve_event_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get('schema', '') in SESSION_EVENT_SCHEMAS:
        return _dict_items(payload.get('events', []))
    if _dict_items(payload.get('observations')):
        return _merge_observation_items(payload, 'events')
    return _dict_items(payload.get('events'))


def _resolve_annotation_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get('schema', '').startswith('pybehaviorlog-'):
        return _dict_items(payload.get('annotations', []))
    return _merge_observation_items(payload, 'annotations')


def _resolve_segment_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get('schema', '').startswith('pybehaviorlog-'):
        return _dict_items(payload.get('segments', []))
    return _merge_observation_items(payload, 'segments')


def _normalize_event_item(item: dict[str, Any]) -> dict[str, Any]:
    behavior = item.get('behavior') or item.get('code') or item.get('behavior_code') or item.get('event') or ''
    frame_token = str(item.get('frame_index') or item.get('frame') or '').strip()
    return {
        'time': _normalize_time(item.get('time') or item.get('timestamp_seconds') or item.get('start')),
        'behavior': str(behavior),
        'event_kind': str(item.get('event_kind') or item.get('type') or 'point').lower(),
        'modifiers': _string_list(item.get('modifiers')),
        'subjects': _string_list(item.get('subjects') or item.get('subject')),
        'comment': str(
            item.get('comment') or item.get('comment_start') or item.get('image_path') or ''
        ),
        'frame_index': int(frame_token) if frame_token else None,
    }


def _normalize_annotation_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'time': _normalize_time(item.get('timestamp_seconds') or item.get('time')),
        'text': str(item.get('text') or item.get('note') or ''),
    }


def _normalize_segment_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'title': str(item.get('title') or ''),
        'start': _normalize_time(item.get('start_seconds') or item.get('start')),
        'end': _normalize_time(item.get('end_seconds') or item.get('end')),
        'status': str(item.get('status') or ''),
    }


def _normalize_variables(payload: dict[str, Any]) -> dict[str, str]:
    variables = payload.get('variables') or payload.get('independent_variables') or {}
    if not isinstance(variables, dict):
        return {}
    return {str(key): str(value) for key, value in sorted(variables.items())}


def normalize_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize BORIS / PyBehaviorLog / CowLog session-like payloads for round-trip checks."""
    events = [_normalize_event_item(item) for item in _resolve_event_items(payload)]
    events.sort(key=lambda item: (item['time'], item['behavior'], item['event_kind']))
    annotations = [_normalize_annotation_item(item) for item in _resolve_annotation_items(payload)]
    annotations.sort(key=lambda item: (item['time'], item['text']))
    segments = [_normalize_segment_item(item) for item in _resolve_segment_items(payload)]
    segments.sort(key=lambda item: (item['start'], item['end'], item['title']))
    return {
        'schema_family': str(payload.get('schema') or 'unknown'),
        'events': events,
        'annotations': annotations,
        'variables': _normalize_variables(payload),
        'media_paths': sorted(
            _string_list(payload.get('media_paths') or payload.get('image_paths'))
        ),
        'segments': segments,
    }


def compare_session_payloads(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Compare two normalized session payloads and return a compact diff report."""
    expected_normalized = normalize_session_payload(expected)
    actual_normalized = normalize_session_payload(actual)
    mismatches: list[str] = []
    if expected_normalized['events'] != actual_normalized['events']:
        mismatches.append('events')
    if expected_normalized['annotations'] != actual_normalized['annotations']:
        mismatches.append('annotations')
    if expected_normalized['variables'] != actual_normalized['variables']:
        mismatches.append('variables')
    if expected_normalized.get('media_paths') != actual_normalized.get('media_paths'):
        mismatches.append('media_paths')
    if expected_normalized.get('segments') != actual_normalized.get('segments'):
        mismatches.append('segments')
    return {
        'equivalent': not mismatches,
        'mismatches': mismatches,
        'expected': expected_normalized,
        'actual': actual_normalized,
    }


def _item_names(value: Any, *, key: str = 'name', fallback: str = 'label') -> list[str]:
    results = []
    for item in _as_list(value):
        if isinstance(item, dict):
            results.append(str(item.get(key) or item.get(fallback) or ''))
        else:
            results.append(str(item))
    return sorted(item for item in results if item)


def _project_session_titles(payload: dict[str, Any]) -> list[str]:
    sessions = payload.get('sessions') or payload.get('observations') or []
    session_titles = []
    for item in _dict_items(sessions):
        if item.get('title') or item.get('description'):
            session_titles.append(str(item.get('title') or item.get('description') or ''))
            continue
        observations = item.get('observations')
        for observation in _dict_items(observations):
            session_titles.append(
                str(observation.get('title') or observation.get('description') or '')
            )
    return sorted(item for item in session_titles if item)


def normalize_project_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize project-like payloads for BORIS/PyBehaviorLog round-trip comparisons."""
    return {
        'schema_family': str(payload.get('schema') or 'unknown'),
        'categories': _item_names(payload.get('categories')),
        'behaviors': _item_names(payload.get('behaviors')),
        'modifiers': _item_names(payload.get('modifiers')),
        'subject_groups': _item_names(payload.get('subject_groups')),
        'subjects': _item_names(payload.get('subjects')),
        'variables': _item_names(
            payload.get('variables') or payload.get('independent_variables'),
            key='label',
            fallback='name',
        ),
        'templates': _item_names(payload.get('observation_templates')),
        'sessions': _project_session_titles(payload),
    }


def compare_project_payloads(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_normalized = normalize_project_payload(expected)
    actual_normalized = normalize_project_payload(actual)
    mismatches = [
        key
        for key in (
            'categories',
            'behaviors',
            'modifiers',
            'subject_groups',
            'subjects',
            'variables',
            'templates',
            'sessions',
        )
        if expected_normalized[key] != actual_normalized[key]
    ]
    return {
        'equivalent': not mismatches,
        'mismatches': mismatches,
        'expected': expected_normalized,
        'actual': actual_normalized,
    }


def build_roundtrip_report(
    expected: dict[str, Any], actual: dict[str, Any], family: str
) -> dict[str, Any]:
    """Build a machine-readable round-trip report for CI and fixture certification."""
    comparator = compare_project_payloads if family == 'project' else compare_session_payloads
    comparison = comparator(expected, actual)
    return {
        'family': family,
        'equivalent': comparison['equivalent'],
        'mismatches': comparison['mismatches'],
        'expected': comparison['expected'],
        'actual': comparison['actual'],
    }

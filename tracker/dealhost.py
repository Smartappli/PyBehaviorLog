from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlparse

DEFAULT_DEALHOST_SDK_MODULE = 'dealhost_sdk'
DEALHOST_SDK_ENV = 'DEALHOST_SDK_MODULE'


def _env_value(environ: dict[str, str], name: str, default: str = '') -> str:
    return str(environ.get(name, default) or '').strip()


def _split_env(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


def _unique(items: list[str]) -> list[str]:
    seen = set()
    results = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            results.append(item)
    return results


def _host_from_value(value: str) -> str:
    parsed = urlparse(value if '://' in value else f'//{value}')
    return parsed.hostname or value.split('/')[0].split(':')[0]


def _origin_from_value(value: str) -> str:
    if value.startswith(('http://', 'https://')):
        parsed = urlparse(value)
        if parsed.netloc:
            return f'{parsed.scheme}://{parsed.netloc}'
    host = _host_from_value(value)
    if host == '*':
        return ''
    return f'https://{host}' if host else ''


def dealhost_hosts_from_env(environ: dict[str, str]) -> list[str]:
    values: list[str] = []
    for name in (
        'DEALHOST_ALLOWED_HOSTS',
        'DEALHOST_APP_HOST',
        'DEALHOST_PUBLIC_HOST',
        'DEALHOST_APP_DOMAIN',
        'DEALHOST_DOMAIN',
        'DEALHOST_APP_URL',
        'DEALHOST_PUBLIC_URL',
    ):
        for item in _split_env(_env_value(environ, name)):
            host = _host_from_value(item)
            if host:
                values.append(host)
    return _unique(values)


def dealhost_origins_from_env(environ: dict[str, str]) -> list[str]:
    values: list[str] = []
    for name in (
        'DEALHOST_CSRF_TRUSTED_ORIGINS',
        'DEALHOST_APP_URL',
        'DEALHOST_PUBLIC_URL',
        'DEALHOST_ALLOWED_HOSTS',
        'DEALHOST_APP_HOST',
        'DEALHOST_PUBLIC_HOST',
        'DEALHOST_APP_DOMAIN',
        'DEALHOST_DOMAIN',
    ):
        for item in _split_env(_env_value(environ, name)):
            origin = _origin_from_value(item)
            if origin:
                values.append(origin)
    return _unique(values)


def dealhost_sdk_module_name(environ: dict[str, str]) -> str:
    return (
        _env_value(environ, DEALHOST_SDK_ENV, DEFAULT_DEALHOST_SDK_MODULE)
        or DEFAULT_DEALHOST_SDK_MODULE
    )


def load_dealhost_sdk(module_name: str = DEFAULT_DEALHOST_SDK_MODULE):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise RuntimeError(
                f'Dealhost SDK module "{module_name}" is installed but one of its '
                f'dependencies is missing: "{exc.name}".'
            ) from exc
        raise RuntimeError(
            f'Dealhost SDK module "{module_name}" is not installed. '
            f'Set {DEALHOST_SDK_ENV} if Dealhost uses another package name.'
        ) from exc


def dealhost_sdk_status(environ: dict[str, str]) -> dict[str, object]:
    module_name = dealhost_sdk_module_name(environ)
    status: dict[str, object] = {
        'module': module_name,
        'available': False,
        'version': None,
    }
    try:
        sdk_module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            status['error'] = f'missing dependency: {exc.name}'
        return status
    status['available'] = True
    try:
        status['version'] = version(module_name.replace('_', '-'))
    except PackageNotFoundError:
        status['version'] = getattr(sdk_module, '__version__', None)
    return status


def build_dealhost_runtime_manifest(environ: dict[str, str]) -> dict[str, object]:
    return {
        'profile': 'dealhost-container',
        'enabled': _env_value(environ, 'DEALHOST_ENABLED').lower() in {'1', 'true', 'yes', 'on'},
        'port_env': 'PORT',
        'port': _env_value(environ, 'PORT', '8000'),
        'public_hosts': dealhost_hosts_from_env(environ),
        'public_origins': dealhost_origins_from_env(environ),
        'health_path': '/health/',
        'release_path': '/release.json',
        'database_url_configured': bool(_env_value(environ, 'DATABASE_URL')),
        'redis_url_configured': bool(_env_value(environ, 'REDIS_URL')),
        'cache_backend': _env_value(environ, 'PYBEHAVIORLOG_CACHE_BACKEND', 'redis'),
        'sdk': dealhost_sdk_status(environ),
    }

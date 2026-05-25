# Dealhost deployment profile

## Current finding

No public Python package or documentation for a hosting platform named
`Dealhost` was found during the implementation pass. Public search results show:

- `dealcloud-sdk`, which belongs to DealCloud/Intapp and is not a hosting SDK.
- `dealhost.in`, which presents DealHost Solutions as a hosting purchase and
  cost-optimization service rather than a PaaS with a deploy SDK.

For that reason, this repository does not pin a non-verifiable `dealhost-sdk`
dependency. Instead it exposes a Dealhost-ready container profile and a lazy SDK
boundary. If Dealhost provides a private or differently named SDK, set
`DEALHOST_SDK_MODULE` to that importable module name and run the SDK check.

## Runtime contract

The application is container-ready for Dealhost-like platforms that provide:

- an HTTP port through `PORT`
- a PostgreSQL URL through `DATABASE_URL`
- optional Redis through `REDIS_URL`
- a public URL through `DEALHOST_APP_URL`
- persistent media storage mounted at `MEDIA_ROOT`

Use `deploy/dealhost.env.example` as the environment template.

## Build and start

The Docker image starts Granian with:

```bash
granian --interface asgi --host 0.0.0.0 --port ${PORT:-8000} --workers ${GRANIAN_WORKERS:-2} --blocking-threads ${GRANIAN_BLOCKING_THREADS:-4} config.asgi:application
```

The entrypoint runs migrations and static collection by default. Disable those
only when the platform has a separate release phase:

```bash
RUN_MIGRATIONS=0
RUN_COLLECTSTATIC=0
```

## Health and release endpoints

- `/health/` returns a small status payload.
- `/release.json` returns release and deployment metadata, including Dealhost
  host/origin detection and SDK availability.

You can inspect the same profile from the command line:

```bash
python manage.py dealhost_manifest
python manage.py dealhost_manifest --sdk-check
```

`--sdk-check` imports the module configured by `DEALHOST_SDK_MODULE` and fails
if it is not available.

## Cache options

Use Redis for production when available:

```bash
PYBEHAVIORLOG_CACHE_BACKEND=redis
REDIS_URL=redis://...
```

For a small single-instance Dealhost deployment without Redis:

```bash
PYBEHAVIORLOG_CACHE_BACKEND=locmem
```

Do not use `locmem` for horizontally scaled deployments.

## SDK handoff

When the official Dealhost SDK is available:

1. Add the exact package and version to `requirements-dealhost.txt`.
2. Set `DEALHOST_SDK_MODULE` if the import name is not `dealhost_sdk`.
3. Run `python manage.py dealhost_manifest --sdk-check` in CI.
4. Add a real client wrapper only after the SDK authentication and deployment
   APIs are documented.

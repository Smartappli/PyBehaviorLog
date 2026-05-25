# Deployment notes

## Recommended stack

- Python 3.13
- Django 6.0.5
- Granian
- PostgreSQL 18
- Redis 8

## Docker workflow

1. Copy the environment file:

   ```bash
   cp .env.example .env
   ```

2. Adjust secrets and hosts.

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Create the first administrator:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## Static files

The entrypoint automatically runs:

- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`

## Production hardening checklist

- set `DJANGO_DEBUG=0`
- set a strong `DJANGO_SECRET_KEY`
- configure `DJANGO_ALLOWED_HOSTS`
- configure `DJANGO_CSRF_TRUSTED_ORIGINS`
- set `SESSION_COOKIE_SECURE=1`
- set `CSRF_COOKIE_SECURE=1`
- place the app behind TLS
- use durable PostgreSQL and Redis volumes

## Test and lint commands

```bash
python manage.py test
coverage run manage.py test
coverage report --fail-under=80
pre-commit run --all-files
```


## Local ASGI run

Use Granian directly to mirror production ASGI behavior:

```bash
granian --interface asgi --host 127.0.0.1 --port 8000 config.asgi:application
```

## Dealhost-compatible container profile

The application now supports a Dealhost-style container deployment profile.
Because no public Dealhost Python hosting SDK could be verified, the integration
is intentionally split into:

- container/runtime compatibility through `PORT`, `DATABASE_URL`, optional
  `REDIS_URL`, and `DEALHOST_APP_URL`
- lazy SDK detection through `DEALHOST_SDK_MODULE`
- a machine-readable profile from `python manage.py dealhost_manifest`

Use:

```bash
python manage.py dealhost_manifest
python manage.py dealhost_manifest --sdk-check
```

The Docker image uses `${PORT:-8000}` and exposes `/health/` for platform health
checks. See `docs/dealhost.md` and `deploy/dealhost.env.example`.

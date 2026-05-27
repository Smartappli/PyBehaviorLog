FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gettext \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY manage.py entrypoint.sh ./
COPY config ./config
COPY tracker ./tracker
COPY templates ./templates
COPY static ./static
COPY locale ./locale
COPY deploy ./deploy

RUN addgroup --system pybehaviorlog \
    && adduser --system --ingroup pybehaviorlog pybehaviorlog \
    && mkdir -p /app/staticfiles /app/media \
    && chmod +x /app/entrypoint.sh \
    && chown -R pybehaviorlog:pybehaviorlog /app

USER pybehaviorlog

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD python -c "import json, os, sys, urllib.request; port=os.getenv('PORT', '8000'); data=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/health/', timeout=3)); sys.exit(0 if data.get('status') == 'ok' else 1)"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "-c", "granian --interface asgi --host 0.0.0.0 --port ${PORT:-8000} --workers ${GRANIAN_WORKERS:-2} --blocking-threads ${GRANIAN_BLOCKING_THREADS:-4} config.asgi:application"]

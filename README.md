
# PyBehaviorLog V6

PyBehaviorLog is a Django 6.0.3 behavioral observation application inspired by CowLog/BORIS workflows.

## Stack

- Python 3.13+
- Django 6.0.3
- openpyxl 3.1.5
- SQLite by default

## Main features included in this archive

- projects, collaborators, videos, sessions
- point/state behaviors with keyboard bindings
- modifiers
- synchronized videos
- event logging and annotations
- CSV / TSV / JSON / XLSX exports
- basic V6 model groundwork for:
  - subjects
  - independent variables
  - live sessions
  - frame index support

## Quick start

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Development setup

```bash
pip install -r requirements-dev.txt
pre-commit install
```

Run checks locally:

```bash
pre-commit run --all-files
coverage run manage.py test
coverage report --fail-under=80
```

## License

This archive is marked for **AGPL-3.0** distribution.

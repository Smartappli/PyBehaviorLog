
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

## GitHub Actions

The repository includes `.github/workflows/ci.yml` to run:

- pre-commit
- Django unit tests
- coverage gate at 80%

on every push and pull request with Python 3.13.

## Notes

I prepared this archive for Python 3.13 minimum. That should not negatively impact Django 6.0.3 usage because Django 6.0 supports Python 3.13. Keep 3.13 as the default runtime for local development and CI. citeturn931282search0turn931282search1

## License

This archive is marked for **AGPL-3.0** distribution.

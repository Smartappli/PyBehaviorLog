# Contributing to PyBehaviorLog

Thanks for helping improve PyBehaviorLog. This project is a Django application
for behavioral observation workflows, including video-assisted coding,
structured ethograms, BORIS/CowLog interoperability, review queues, exports, and
deployment tooling.

## Before You Start

- Check existing issues and pull requests to avoid duplicate work.
- Keep changes focused. Separate unrelated fixes into separate pull requests.
- Do not include private datasets, credentials, production secrets, or research
  subject data in issues, tests, fixtures, screenshots, or commits.
- By contributing, you agree that your contribution is provided under the
  repository license, AGPL-3.0-only.

## Development Setup

PyBehaviorLog targets Python 3.13+.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

For an ASGI-parity local run, use Granian:

```bash
granian --interface asgi --host 127.0.0.1 --port 8000 config.asgi:application
```

## Quality Checks

Run the checks that match the scope of your change:

```bash
python manage.py test
coverage run manage.py test
coverage report --fail-under=81
pre-commit run --all-files
```

Use focused tests while developing, then run the broader suite before opening a
pull request.

## Django Changes

- Include migrations for model changes.
- Keep data migrations deterministic and safe to run in CI and production.
- Update forms, views, templates, and tests together when behavior changes.
- Preserve existing project-membership and review-workflow permissions unless a
  change explicitly intends to modify authorization behavior.

## Compatibility Changes

PyBehaviorLog includes BORIS and CowLog import/export support. When changing
compatibility behavior:

- Add or update fixtures under `tracker/tests/fixtures/` when the exchange
  format changes.
- Cover round-trip behavior with tests.
- Document known limitations in `docs/compatibility.md` or
  `docs/compatibility_matrix.md`.
- Avoid compatibility claims that are not backed by fixtures, documented public
  formats, or repeatable tests.

## Documentation and Localization

- Update `README.md` or files in `docs/` when setup, deployment, compatibility,
  or user-visible behavior changes.
- Keep terminology consistent across templates, forms, documentation, and
  translations.
- When changing user-visible strings, update translation catalogs where
  practical and make sure untranslated fallbacks remain clear.

## Pull Request Expectations

Pull requests should include:

- A concise summary of the change.
- The reason the change is needed.
- Tests or a clear explanation of why tests are not applicable.
- Notes about migrations, deployment impact, data compatibility, or security
  impact when relevant.
- Screenshots or short recordings for UI changes when they make review easier.


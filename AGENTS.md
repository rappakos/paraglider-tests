# paraglider-tests — agent guidance

FastAPI + Jinja2 app that collects DHV and Air Turquoise certification reports and
compares gliders.

## Running

- From the repo root: `.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 3978`
- On the server the nginx subfolder comes from `GLIDER_TESTS_APP_ROOT_PATH`.
- Known gap: the POST form actions in `templates/reports.html` and the redirects in
  `views.py` use `/{org}` without the prefix. Don't copy that pattern.
- OCR fallback for broken Air Turquoise PDFs needs the system packages
  `tesseract-ocr` and `poppler-utils`.
- The app is also run on Android in Termux (see `README.md`). Mention it if a new
  dependency is heavy or needs native builds.

## Layout

- `main.py` → `glider_tests_app/routes.py` → `views.py` → `db.py`; schema in `init_db.sql`.
- Loaders: `glider_tests_app/dhv_loader.py`, `airturquoise_loader.py`.
- `manufacturer_data/`: glider specs from manufacturers.
- In `routes.py`, `/{org}` is a catch-all. `api_router` must stay included first, and
  new fixed paths must not be shadowed by it.

## Data

- `glider_tests.db` at the repo root. The path is defined twice, in
  `glider_tests_app/db.py` and `manufacturer_data/manufacturer_service.py`.
- Back up as `glider_tests_backup_YYYYMMDD.db` before schema changes or bulk reloads.
  Don't delete older backups.
- `data/` holds downloaded reports.
- Air Turquoise download actions only consider reports from
  `AIR_TURQUOISE_PDF_CUTOFF_DATE` (in `db.py`) onwards.

## Verification

- `.venv/bin/python -m pytest`
- `tests/test_base_loader.py` needs `pytest-asyncio`, which is missing from
  `requirements.txt`. Without it, collection fails; the other tests run with
  `--ignore=tests/test_base_loader.py`.
- The `client` fixtures in `tests/conftest.py` import the real app, so route tests run
  against the working `glider_tests.db`. Don't add tests that POST or otherwise write
  until the database path is redirected to a temporary file, in both places above.
- For parser changes, run the affected report through the loader and compare the
  extracted values with the source document.

# Development

Python 3.11+ and stdlib-only runtime; tests use pytest, Ruff and build.

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
python tools/secret_scan.py
python tools/audit_docs.py
python tools/manual.py --check
python -m build
```

Generate catalog/maps/reference with tools/catalog.py, tools/cli_map.py and tools/manual.py.
Document examples are parsed without executing operations. Keep registry IDs stable,
aliases collision-free, receipt/model schemas explicit and fixture evidence labeled.
AI transports are mocked in CI. Live calls require explicit account/model/consent and
are never part of default tests. Retain serial CI and at most two background processes.
Review licensing/provenance and CREDITS for every meaningful external influence.

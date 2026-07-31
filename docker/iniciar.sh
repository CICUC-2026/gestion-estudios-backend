#!/bin/sh
set -eu

alembic upgrade head
python -m app.scripts.cargar_datos_demo || true
python -m app.scripts.importar_catalogo_csv app/scripts/catalogo_oncologia_cicuc.csv || true
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

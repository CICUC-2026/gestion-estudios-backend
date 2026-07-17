# Gestión de estudios clínicos — Backend

API y reglas de negocio de la plataforma CICUC.

## Inicio local

```bash
cp .env.example .env
docker compose up --build
```

La API queda disponible en `http://localhost:8000`, su salud en `/api/v1/salud` y OpenAPI en `/documentacion-api`.

## Desarrollo sin contenedores

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Verificación:

```bash
ruff check .
ruff format --check .
mypy app tests
pytest
alembic upgrade head --sql
```

## Stack decidido

- Python y FastAPI.
- SQLAlchemy y Alembic.
- PostgreSQL.
- Pydantic y Pytest.
- API REST versionada bajo `/api/v1`.

## Principios

- monolito modular por dominios;
- autorización en backend por acción y recurso;
- migraciones reproducibles y restricciones en base de datos;
- auditoría de acciones relevantes;
- datos ficticios fuera de producción;
- sin IA ni decisión automática de elegibilidad.

Documentación y backlog: <https://github.com/CICUC-2026/gestion-estudios-documentacion>.

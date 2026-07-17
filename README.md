# Gestión de estudios clínicos — Backend

API y reglas de negocio de la plataforma CICUC.

## Estado

Tanda 0: repositorio creado; implementación técnica pendiente de HU-001.

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

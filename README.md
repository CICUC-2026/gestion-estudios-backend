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

## Crear el primer administrador

Después de aplicar migraciones, ejecutar de forma interactiva:

```bash
python -m app.scripts.crear_administrador
```

La contraseña se solicita sin mostrarla ni incluirla en el historial del shell. No existe registro público.

## Autenticación inicial

- `POST /api/v1/autenticacion/ingresar` crea una sesión opaca expirable.
- `GET /api/v1/autenticacion/yo` valida sesión y devuelve el perfil mínimo.
- `POST /api/v1/autenticacion/salir` revoca la sesión actual.
- `GET /api/v1/autenticacion/sesiones` lista sesiones propias.
- `DELETE /api/v1/autenticacion/sesiones/{id}` revoca una sesión propia.
- `POST /api/v1/autenticacion/cambiar-contrasena` cambia la contraseña y revoca las demás sesiones.
- `POST /api/v1/usuarios` crea cuentas, solo para administración.
- `PATCH /api/v1/usuarios/{id}/estado` activa o desactiva cuentas y revoca sesiones al desactivar.

Las contraseñas utilizan Argon2. Los tokens se almacenan únicamente como SHA-256, los errores de ingreso no revelan el estado de una cuenta y los intentos fallidos aplican un bloqueo temporal configurable.

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

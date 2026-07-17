from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.base_datos.sesion import FabricaSesiones
from app.dominios.autenticacion.modelos import RegistroAuditoria, Sesion, Usuario


def encabezado(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_no_existe_registro_publico(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/v1/registrar",
        json={"correo": "persona@example.com", "contrasena": "secreto"},
    )

    assert respuesta.status_code == 404


def test_administrador_crea_y_desactiva_cuenta(cliente: TestClient, token_admin: str) -> None:
    creada = cliente.post(
        "/api/v1/usuarios",
        headers=encabezado(token_admin),
        json={
            "nombres": "María",
            "apellidos": "Médica",
            "correo": "medica@example.com",
            "contrasena_inicial": "Contrasena-Demo-2026",
        },
    )
    assert creada.status_code == 201
    usuario_id = creada.json()["id"]
    assert creada.json()["correo"] == "medica@example.com"

    ingreso = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": "medica@example.com", "contrasena": "Contrasena-Demo-2026"},
    )
    assert ingreso.status_code == 200

    desactivada = cliente.patch(
        f"/api/v1/usuarios/{usuario_id}/estado",
        headers=encabezado(token_admin),
        json={"activo": False},
    )
    assert desactivada.status_code == 200
    assert desactivada.json()["activo"] is False
    assert (
        cliente.get(
            "/api/v1/autenticacion/yo",
            headers=encabezado(ingreso.json()["token_acceso"]),
        ).status_code
        == 401
    )

    with FabricaSesiones() as sesion_db:
        cuenta = sesion_db.scalar(select(Usuario).where(Usuario.id == usuario_id))
        assert cuenta is not None
        assert cuenta.contrasena_hash != "Contrasena-Demo-2026"
        assert cuenta.contrasena_hash.startswith("$argon2")
        acciones = sesion_db.scalars(
            select(RegistroAuditoria.accion).order_by(RegistroAuditoria.fecha)
        ).all()
        assert "usuario.crear" in acciones
        assert "usuario.desactivar" in acciones


def test_logout_revoca_token(cliente: TestClient, token_admin: str) -> None:
    assert (
        cliente.get("/api/v1/autenticacion/yo", headers=encabezado(token_admin)).status_code == 200
    )
    assert (
        cliente.post("/api/v1/autenticacion/salir", headers=encabezado(token_admin)).status_code
        == 204
    )
    respuesta = cliente.get("/api/v1/autenticacion/yo", headers=encabezado(token_admin))

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "SESION_INVALIDA"


def test_sesion_expirada_se_rechaza(cliente: TestClient, token_admin: str) -> None:
    with FabricaSesiones() as sesion_db:
        sesion = sesion_db.scalar(select(Sesion))
        assert sesion is not None
        sesion.expira_en = datetime.now(UTC) - timedelta(seconds=1)
        sesion_db.commit()

    respuesta = cliente.get("/api/v1/autenticacion/yo", headers=encabezado(token_admin))
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["codigo"] == "SESION_INVALIDA"


def test_usuario_revoca_otra_sesion(
    cliente: TestClient, administrador: Usuario, token_admin: str
) -> None:
    segundo_ingreso = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Contrasena-Demo-2026"},
    )
    segundo_token = segundo_ingreso.json()["token_acceso"]
    sesiones = cliente.get("/api/v1/autenticacion/sesiones", headers=encabezado(token_admin)).json()
    otra = next(sesion for sesion in sesiones if not sesion["es_actual"])

    respuesta = cliente.delete(
        f"/api/v1/autenticacion/sesiones/{otra['id']}", headers=encabezado(token_admin)
    )

    assert respuesta.status_code == 204
    assert (
        cliente.get("/api/v1/autenticacion/yo", headers=encabezado(segundo_token)).status_code
        == 401
    )
    assert (
        cliente.get("/api/v1/autenticacion/yo", headers=encabezado(token_admin)).status_code == 200
    )


def test_errores_no_revelan_estado_de_cuenta(cliente: TestClient, administrador: Usuario) -> None:
    inexistente = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": "nadie@example.com", "contrasena": "incorrecta"},
    )
    incorrecta = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "incorrecta"},
    )

    assert inexistente.status_code == incorrecta.status_code == 401
    assert inexistente.json() == incorrecta.json()
    assert inexistente.json()["error"]["codigo"] == "CREDENCIALES_INVALIDAS"


def test_bloqueo_temporal_tras_intentos_fallidos(
    cliente: TestClient, administrador: Usuario
) -> None:
    for _ in range(5):
        respuesta = cliente.post(
            "/api/v1/autenticacion/ingresar",
            json={"correo": administrador.correo, "contrasena": "incorrecta"},
        )
        assert respuesta.status_code == 401

    aun_bloqueada = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Contrasena-Demo-2026"},
    )
    assert aun_bloqueada.status_code == 401
    assert aun_bloqueada.json()["error"]["codigo"] == "CREDENCIALES_INVALIDAS"


def test_ruta_administrativa_rechaza_usuario_sin_permiso(
    cliente: TestClient, token_admin: str
) -> None:
    creada = cliente.post(
        "/api/v1/usuarios",
        headers=encabezado(token_admin),
        json={
            "nombres": "Solo",
            "apellidos": "Usuario",
            "correo": "usuario@example.com",
            "contrasena_inicial": "Contrasena-Demo-2026",
        },
    )
    token_usuario = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": "usuario@example.com", "contrasena": "Contrasena-Demo-2026"},
    ).json()["token_acceso"]

    denegada = cliente.post(
        "/api/v1/usuarios",
        headers=encabezado(token_usuario),
        json={
            "nombres": "Otra",
            "apellidos": "Persona",
            "correo": "otra@example.com",
            "contrasena_inicial": "Contrasena-Demo-2026",
        },
    )
    assert creada.status_code == 201
    assert denegada.status_code == 403
    assert denegada.json()["error"]["codigo"] == "PERMISO_DENEGADO"


def test_cambio_de_contrasena_revoca_otras_sesiones(
    cliente: TestClient, administrador: Usuario, token_admin: str
) -> None:
    segundo_token = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Contrasena-Demo-2026"},
    ).json()["token_acceso"]

    cambio = cliente.post(
        "/api/v1/autenticacion/cambiar-contrasena",
        headers=encabezado(token_admin),
        json={
            "contrasena_actual": "Contrasena-Demo-2026",
            "contrasena_nueva": "Nueva-Contrasena-2026",
        },
    )

    assert cambio.status_code == 204
    assert (
        cliente.get("/api/v1/autenticacion/yo", headers=encabezado(token_admin)).status_code == 200
    )
    assert (
        cliente.get("/api/v1/autenticacion/yo", headers=encabezado(segundo_token)).status_code
        == 401
    )
    anterior = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Contrasena-Demo-2026"},
    )
    nueva = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Nueva-Contrasena-2026"},
    )
    assert anterior.status_code == 401
    assert nueva.status_code == 200

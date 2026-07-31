from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dominios.autenticacion.esquemas import CrearUsuario
from app.dominios.autenticacion.modelos import RolUsuario
from app.dominios.autenticacion.servicio import crear_usuario


def test_administrador_asigna_y_modifica_roles_de_usuario(
    cliente: TestClient, token_admin: str
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 1. Crear usuario con rol de coordinador
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json={
            "nombres": "Carlos",
            "apellidos": "Coordinador",
            "correo": "coordinador@example.com",
            "contrasena_inicial": "Contrasena-Coordinador-2026",
            "roles": ["coordinador"],
        },
        headers=headers,
    )
    assert respuesta.status_code == 201
    datos_u = respuesta.json()
    assert datos_u["roles"] == ["coordinador"]
    usuario_id = datos_u["id"]

    # 2. Modificar roles a investigador principal y auditor
    respuesta_put = cliente.put(
        f"/api/v1/usuarios/{usuario_id}/roles",
        json={"roles": ["investigador_principal", "auditor"]},
        headers=headers,
    )
    assert respuesta_put.status_code == 200
    roles_actualizados = respuesta_put.json()["roles"]
    assert set(roles_actualizados) == {"investigador_principal", "auditor"}

    # 3. Listar usuarios y verificar roles
    respuesta_lista = cliente.get("/api/v1/usuarios", headers=headers)
    assert respuesta_lista.status_code == 200
    usuarios = respuesta_lista.json()
    coordinador_encontrado = next(u for u in usuarios if u["id"] == usuario_id)
    assert set(coordinador_encontrado["roles"]) == {"investigador_principal", "auditor"}


def test_usuario_sin_rol_requerido_es_rechazado(
    cliente: TestClient, base_limpia: None, sesion_db: Session
) -> None:
    # Crear usuario médico sin rol de administrador
    medico = crear_usuario(
        sesion_db,
        CrearUsuario(
            nombres="Elena",
            apellidos="Médico",
            correo="elena@example.com",
            contrasena_inicial="Contrasena-Elena-2026",
            roles=[RolUsuario.MEDICO_INVESTIGADOR],
        ),
        actor_id=None,
        direccion_ip="127.0.0.1",
    )

    resp_login = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": medico.correo, "contrasena": "Contrasena-Elena-2026"},
    )
    assert resp_login.status_code == 200
    token_medico = resp_login.json()["token_acceso"]

    # Intentar acceder a endpoint administrativo de usuarios
    resp_admin = cliente.get(
        "/api/v1/usuarios",
        headers={"Authorization": f"Bearer {token_medico}"},
    )
    assert resp_admin.status_code == 403
    assert resp_admin.json()["error"]["codigo"] == "PERMISO_DENEGADO"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dominios.autenticacion.esquemas import CrearUsuario
from app.dominios.autenticacion.modelos import RolUsuario
from app.dominios.autenticacion.servicio import crear_usuario


@pytest.fixture
def token_coordinador(cliente: TestClient, sesion_db: Session) -> str:
    coord = crear_usuario(
        sesion_db,
        CrearUsuario(
            nombres="Clara",
            apellidos="Coordinadora",
            correo="coordinadora@example.com",
            contrasena_inicial="Contrasena-Coord-2026",
            roles=[RolUsuario.COORDINADOR],
        ),
        actor_id=None,
        direccion_ip="127.0.0.1",
    )
    resp = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": coord.correo, "contrasena": "Contrasena-Coord-2026"},
    )
    return str(resp.json()["token_acceso"])


@pytest.fixture
def token_medico(cliente: TestClient, sesion_db: Session) -> str:
    med = crear_usuario(
        sesion_db,
        CrearUsuario(
            nombres="Mateo",
            apellidos="Médico",
            correo="mateo@example.com",
            contrasena_inicial="Contrasena-Mateo-2026",
            roles=[RolUsuario.MEDICO_INVESTIGADOR],
        ),
        actor_id=None,
        direccion_ip="127.0.0.1",
    )
    resp = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": med.correo, "contrasena": "Contrasena-Mateo-2026"},
    )
    return str(resp.json()["token_acceso"])


def test_flujo_completo_estudio_protocolos_inmutables_y_comparacion(
    cliente: TestClient, token_coordinador: str, token_admin: str, token_medico: str
) -> None:
    headers_coord = {"Authorization": f"Bearer {token_coordinador}"}
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    headers_medico = {"Authorization": f"Bearer {token_medico}"}

    # 1. Crear estudio por parte del coordinador
    resp_estudio = cliente.post(
        "/api/v1/estudios",
        json={
            "codigo_interno": "ONCO-2026-01",
            "titulo": "Estudio de Inmunoterapia en Pulmón Avanzado",
            "patrocinador": "Laboratorio Farmacéutico Demo",
            "fase": "Fase III",
            "patologia": "Cáncer de Pulmón de Células No Pequeñas",
            "escenario_clinico": "Metastásico",
            "linea_tratamiento": "Segunda línea",
            "centro_atencion": "CICUC Principal",
            "cohortes": [
                {
                    "nombre": "Cohorte A - EGFR Positivo",
                    "descripcion": "Pacientes con mutación EGFR confirmada",
                    "biomarcadores_requeridos": ["EGFR+"],
                    "meta_reclutamiento": 25,
                }
            ],
        },
        headers=headers_coord,
    )
    assert resp_estudio.status_code == 201
    estudio_id = resp_estudio.json()["id"]
    assert resp_estudio.json()["estado"] == "borrador"

    # 2. Agregar Versión 1.0 con criterios
    resp_v1 = cliente.post(
        f"/api/v1/estudios/{estudio_id}/versiones",
        json={
            "numero_version": "v1.0",
            "descripcion_cambios": "Versión inicial del protocolo",
            "criterios": [
                {
                    "tipo": "inclusion",
                    "codigo_criterio": "INC-01",
                    "descripcion": "Edad mayor o igual a 18 años.",
                    "orden": 1,
                    "seccion_fuente": "Sección 4.1",
                },
                {
                    "tipo": "exclusion",
                    "codigo_criterio": "EXC-01",
                    "descripcion": "Metástasis cerebral sintomática no tratada.",
                    "orden": 1,
                    "seccion_fuente": "Sección 4.2",
                },
            ],
        },
        headers=headers_coord,
    )
    assert resp_v1.status_code == 201
    v1_id = resp_v1.json()["id"]

    # 3. Publicar Versión 1.0 por parte del administrador
    resp_pub1 = cliente.post(
        f"/api/v1/estudios/{estudio_id}/versiones/{v1_id}/publicar",
        headers=headers_admin,
    )
    assert resp_pub1.status_code == 200
    assert resp_pub1.json()["es_vigente"] is True
    assert resp_pub1.json()["estado"] == "vigente"

    # Verificar que el estudio ahora esté en estado vigente
    resp_estudio_v = cliente.get(f"/api/v1/estudios/{estudio_id}", headers=headers_coord)
    assert resp_estudio_v.json()["estado"] == "vigente"
    assert resp_estudio_v.json()["version_vigente"]["numero_version"] == "v1.0"

    # 4. Crear Versión 2.0 con enmienda y nuevos criterios
    resp_v2 = cliente.post(
        f"/api/v1/estudios/{estudio_id}/versiones",
        json={
            "numero_version": "v2.0",
            "descripcion_cambios": "Enmienda 1: Inclusión de ECOG 2",
            "criterios": [
                {
                    "tipo": "inclusion",
                    "codigo_criterio": "INC-01",
                    "descripcion": "Edad mayor o igual a 18 años.",
                    "orden": 1,
                },
                {
                    "tipo": "inclusion",
                    "codigo_criterio": "INC-02",
                    "descripcion": "Estado funcional ECOG 0, 1 o 2.",
                    "orden": 2,
                    "seccion_fuente": "Sección 4.1.2",
                },
            ],
        },
        headers=headers_coord,
    )
    assert resp_v2.status_code == 201
    v2_id = resp_v2.json()["id"]

    # 5. Publicar Versión 2.0 y verificar inmutabilidad/reemplazo de v1.0
    resp_pub2 = cliente.post(
        f"/api/v1/estudios/{estudio_id}/versiones/{v2_id}/publicar",
        headers=headers_admin,
    )
    assert resp_pub2.status_code == 200
    assert resp_pub2.json()["es_vigente"] is True

    # Consultar v1.0 y confirmar que quedó en estado 'reemplazada' y es_vigente=False
    resp_check_estudio = cliente.get(f"/api/v1/estudios/{estudio_id}", headers=headers_coord)
    versiones = resp_check_estudio.json()["version_vigente"]
    assert versiones["numero_version"] == "v2.0"

    # 6. Comparar versiones v1.0 y v2.0
    resp_comp = cliente.get(
        f"/api/v1/estudios/{estudio_id}/comparar-versiones?version_v1_id={v1_id}&version_v2_id={v2_id}",
        headers=headers_coord,
    )
    assert resp_comp.status_code == 200
    comp_data = resp_comp.json()
    assert len(comp_data["criterios_agregados"]) == 1
    assert comp_data["criterios_agregados"][0]["codigo_criterio"] == "INC-02"
    assert len(comp_data["criterios_eliminados"]) == 1
    assert comp_data["criterios_eliminados"][0]["codigo_criterio"] == "EXC-01"

    # 7. Verificación de permisos negativos: Médico no puede publicar versión (requiere admin o IP)
    resp_denegada = cliente.post(
        f"/api/v1/estudios/{estudio_id}/versiones/{v2_id}/publicar",
        headers=headers_medico,
    )
    assert resp_denegada.status_code == 403
    assert resp_denegada.json()["error"]["codigo"] == "PERMISO_DENEGADO"

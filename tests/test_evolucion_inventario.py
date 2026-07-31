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


def test_flujo_completo_hu30_hu31_hu32(cliente: TestClient, token_coordinador: str) -> None:
    headers = {"Authorization": f"Bearer {token_coordinador}"}

    # 1. Crear estudio con cohortes y brazos (HU-031)
    res_crear = cliente.post(
        "/api/v1/estudios",
        headers=headers,
        json={
            "codigo_interno": "EST-HU30",
            "titulo": "Estudio Fase 2 en Cáncer Gástrico",
            "patrocinador": "Roche",
            "fase": "Fase 2",
            "patologia": "Cáncer Gástrico",
            "escenario_clinico": "Avanzado",
            "linea_tratamiento": "Primera línea",
            "centro_atencion": "CICUC San Joaquín",
            "estado_operacional": "activado",
            "disponibilidad": "con_cupo",
            "cohortes": [
                {
                    "nombre": "Cohorte HER2+",
                    "patologia": "Cáncer Gástrico",
                    "subtipo_histologico": "HER2 Positivo",
                    "estado_operacional": "activado",
                    "disponibilidad": "con_cupo",
                    "brazos": [
                        {"nombre": "Brazo A: Trastuzumab + Quimioterapia"},
                        {"nombre": "Brazo B: Inmunoterapia + Quimioterapia"},
                    ],
                }
            ],
        },
    )
    assert res_crear.status_code == 201
    estudio = res_crear.json()
    estudio_id = estudio["id"]
    assert estudio["estado_operacional"] == "activado"
    assert estudio["disponibilidad"] == "con_cupo"
    assert len(estudio["cohortes"]) == 1
    assert len(estudio["cohortes"][0]["brazos"]) == 2

    # 2. Modificar Estado Operacional de forma independiente y verificar historial (HU-030)
    res_op = cliente.patch(
        f"/api/v1/estudios/{estudio_id}/estado-operacional",
        headers=headers,
        json={
            "estado_operacional": "cerrado_temporalmente",
            "fuente": "Comunicado del patrocinador 2026-07-31",
            "motivo": "Pausa técnica de enrolamiento",
        },
    )
    assert res_op.status_code == 200
    estudio_op = res_op.json()
    assert estudio_op["estado_operacional"] == "cerrado_temporalmente"
    assert estudio_op["disponibilidad"] == "con_cupo"  # Independiente
    assert len(estudio_op["historial_estados"]) == 1
    assert estudio_op["historial_estados"][0]["campo_modificado"] == "estado_operacional"

    # 3. Modificar Disponibilidad de forma independiente (HU-030)
    res_disp = cliente.patch(
        f"/api/v1/estudios/{estudio_id}/disponibilidad",
        headers=headers,
        json={
            "disponibilidad": "sin_cupo",
            "fuente": "Coordinación de centro",
            "motivo": "Cupos ocupados en San Joaquín",
        },
    )
    assert res_disp.status_code == 200
    estudio_disp = res_disp.json()
    assert estudio_disp["disponibilidad"] == "sin_cupo"
    assert estudio_disp["estado_operacional"] == "cerrado_temporalmente"

    # 4. Reconfirmar vigencia y calcular etiqueta (HU-032)
    res_vig = cliente.post(
        f"/api/v1/estudios/{estudio_id}/reconfirmar-vigencia",
        headers=headers,
        json={
            "fuente_informacion": "Informe mensual de seguimiento",
            "dias_validez": 30,
        },
    )
    assert res_vig.status_code == 200
    estudio_vig = res_vig.json()
    assert estudio_vig["etiqueta_vigencia"] == "vigente"
    assert estudio_vig["fuente_informacion"] == "Informe mensual de seguimiento"

    # 5. Filtrar por estado_operacional y disponibilidad de forma independiente
    res_filtro = cliente.get(
        "/api/v1/estudios?estado_operacional=cerrado_temporalmente&disponibilidad=sin_cupo",
        headers=headers,
    )
    assert res_filtro.status_code == 200
    lista = res_filtro.json()
    assert len(lista) == 1
    assert lista[0]["id"] == estudio_id

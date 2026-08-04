from typing import cast

from fastapi.testclient import TestClient


def test_preseleccion_sintetica_evalua_transiciona_y_audita(
    cliente: TestClient, token_admin: str
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    paciente = cliente.post(
        "/api/v1/pacientes-demo",
        headers=headers,
        json={
            "codigo": "PX-DEMO-PRE-01",
            "rango_etario": "50–64 años",
            "patologia": "Patología ficticia",
        },
    ).json()
    estudio = cliente.post(
        "/api/v1/estudios",
        headers=headers,
        json={
            "codigo_interno": "EST-PRE-DEMO",
            "titulo": "Estudio sintético de preselección",
            "patrocinador": "Demo",
            "fase": "Fase demo",
            "patologia": "Patología ficticia",
            "escenario_clinico": "Escenario ficticio",
            "linea_tratamiento": "Línea ficticia",
        },
    ).json()
    version = cliente.post(
        f"/api/v1/estudios/{estudio['id']}/versiones",
        headers=headers,
        json={
            "numero_version": "1.0",
            "descripcion_cambios": "Versión sintética",
            "criterios": [
                {
                    "tipo": "inclusion",
                    "codigo_criterio": "INC-DEMO",
                    "descripcion": "Criterio exclusivamente ficticio",
                    "orden": 1,
                }
            ],
        },
    ).json()
    criterio_id = version["criterios"][0]["id"]

    creada = cliente.post(
        "/api/v1/preselecciones-demo",
        headers=headers,
        json={
            "paciente_id": paciente["id"],
            "estudio_id": estudio["id"],
            "version_id": version["id"],
            "motivo": "Demostración manual",
        },
    )
    assert creada.status_code == 201
    identificador = creada.json()["id"]
    assert creada.json()["estado"] == "pendiente_revision"

    inicio = cliente.patch(
        f"/api/v1/preselecciones-demo/{identificador}/estado",
        headers=headers,
        json={"estado": "en_revision", "motivo": "Inicio de revisión humana"},
    )
    assert inicio.status_code == 200
    evaluada = cliente.put(
        f"/api/v1/preselecciones-demo/{identificador}/criterios/{criterio_id}",
        headers=headers,
        json={
            "estado": "pendiente_verificar",
            "comentario": "Información ficticia pendiente",
            "fuente": "Fuente sintética",
        },
    )
    assert evaluada.status_code == 200
    assert evaluada.json()["evaluaciones"][0]["estado"] == "pendiente_verificar"

    cerrada = cliente.patch(
        f"/api/v1/preselecciones-demo/{identificador}/estado",
        headers=headers,
        json={
            "estado": "cerrado",
            "motivo": "Fin de demostración",
            "resumen": "Resumen administrativo sintético",
        },
    )
    assert cerrada.status_code == 200
    assert cerrada.json()["estado"] == "cerrado"
    assert len(cerrada.json()["historial"]) == 3
    assert (
        cliente.put(
            f"/api/v1/preselecciones-demo/{identificador}/criterios/{criterio_id}",
            headers=headers,
            json={"estado": "dudoso", "comentario": "No permitido cerrado", "fuente": "Demo"},
        ).status_code
        == 409
    )


def test_preseleccion_rechaza_version_de_otro_estudio(
    cliente: TestClient, token_admin: str
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    paciente = cliente.post(
        "/api/v1/pacientes-demo",
        headers=headers,
        json={"codigo": "PX-DEMO-PRE-02", "rango_etario": "35–49 años", "patologia": "Ficticia"},
    ).json()

    def estudio(codigo: str) -> dict[str, object]:
        return cast(
            dict[str, object],
            cliente.post(
                "/api/v1/estudios",
                headers=headers,
                json={
                    "codigo_interno": codigo,
                    "titulo": codigo,
                    "patrocinador": "Demo",
                    "fase": "Demo",
                    "patologia": "Ficticia",
                    "escenario_clinico": "Ficticio",
                    "linea_tratamiento": "Ficticia",
                },
            ).json(),
        )

    primero, segundo = estudio("EST-PRE-A"), estudio("EST-PRE-B")
    version = cliente.post(
        f"/api/v1/estudios/{primero['id']}/versiones",
        headers=headers,
        json={"numero_version": "1", "descripcion_cambios": "Demo"},
    ).json()
    respuesta = cliente.post(
        "/api/v1/preselecciones-demo",
        headers=headers,
        json={
            "paciente_id": paciente["id"],
            "estudio_id": segundo["id"],
            "version_id": version["id"],
            "motivo": "Debe fallar",
        },
    )
    assert respuesta.status_code == 422

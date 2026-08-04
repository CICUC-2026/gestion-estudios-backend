from fastapi.testclient import TestClient


def test_paciente_demo_persiste_diagnostico_asociacion_y_archivo(
    cliente: TestClient, token_admin: str
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    creado = cliente.post(
        "/api/v1/pacientes-demo",
        headers=headers,
        json={
            "codigo": "PX-DEMO-0042",
            "rango_etario": "50–64 años",
            "patologia": "Patología ficticia A",
        },
    )
    assert creado.status_code == 201
    paciente_id = creado.json()["id"]
    assert creado.json()["sintetico"] is True
    assert len(cliente.get("/api/v1/pacientes-demo", headers=headers).json()) == 1

    diagnostico = cliente.post(
        f"/api/v1/pacientes-demo/{paciente_id}/diagnosticos",
        headers=headers,
        json={
            "diagnostico": "Diagnóstico ficticio",
            "biomarcador": "MARCADOR-DEMO",
            "resultado_biomarcador": "positivo ficticio",
            "fecha": "2026-08-04",
            "fuente": "Fuente sintética",
        },
    )
    assert diagnostico.status_code == 201
    assert (
        len(
            cliente.get(
                f"/api/v1/pacientes-demo/{paciente_id}/diagnosticos", headers=headers
            ).json()
        )
        == 1
    )

    estudio = cliente.post(
        "/api/v1/estudios",
        headers=headers,
        json={
            "codigo_interno": "EST-DEMO-42",
            "titulo": "Estudio completamente ficticio",
            "patologia": "Patología ficticia A",
        },
    )
    assert estudio.status_code == 201
    asociacion = cliente.post(
        f"/api/v1/pacientes-demo/{paciente_id}/estudios",
        headers=headers,
        json={
            "estudio_id": estudio.json()["id"],
            "observaciones": "Revisión administrativa ficticia",
        },
    )
    assert asociacion.status_code == 201
    assert asociacion.json()["estado"] == "pendiente_revision"

    archivado = cliente.patch(
        f"/api/v1/pacientes-demo/{paciente_id}", headers=headers, json={"archivado": True}
    )
    assert archivado.status_code == 200
    assert cliente.get("/api/v1/pacientes-demo", headers=headers).json() == []


def test_paciente_demo_rechaza_identidad_no_sintetica_y_sesion(
    cliente: TestClient, token_admin: str
) -> None:
    assert cliente.get("/api/v1/pacientes-demo").status_code == 401
    respuesta = cliente.post(
        "/api/v1/pacientes-demo",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "codigo": "PACIENTE-REAL",
            "rango_etario": "35–49 años",
            "patologia": "Dato no permitido",
        },
    )
    assert respuesta.status_code == 422

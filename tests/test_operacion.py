from fastapi.testclient import TestClient


def test_tareas_y_reportes_persisten_y_auditan(cliente: TestClient, token_admin: str) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    tarea = cliente.post(
        "/api/v1/tareas", headers=headers, json={"titulo": "Confirmar cupos", "prioridad": "alta"}
    )
    assert tarea.status_code == 201
    assert tarea.json()["estado"] == "pendiente"
    assert len(cliente.get("/api/v1/tareas", headers=headers).json()) == 1
    actualizada = cliente.patch(
        f"/api/v1/tareas/{tarea.json()['id']}",
        headers=headers,
        json={"estado": "completada", "prioridad": "media"},
    )
    assert actualizada.status_code == 200
    assert actualizada.json()["estado"] == "completada"

    reporte = cliente.post(
        "/api/v1/reportes",
        headers=headers,
        json={"nombre": "Corte operativo", "finalidad": "Seguimiento de trabajo pendiente"},
    )
    assert reporte.status_code == 201
    assert reporte.json()["contenido"]["tareas_pendientes"] == 0
    assert reporte.json()["contenido"]["metricas"]["tareas"]["presentacion"] == "<5"
    assert reporte.json()["contenido"]["metricas"]["tareas"]["suprimido"] is True
    assert reporte.json()["contenido"]["advertencia"].startswith("Uso operativo")
    assert reporte.json()["contenido"]["filtros"] == {
        "estudio_id": None,
        "estados_tarea": [],
    }
    assert len(cliente.get("/api/v1/reportes", headers=headers).json()) == 1

    futuro = cliente.post(
        "/api/v1/reportes",
        headers=headers,
        json={
            "nombre": "Corte futuro",
            "finalidad": "Debe rechazarse",
            "fecha_corte": "2099-01-01T00:00:00Z",
        },
    )
    assert futuro.status_code == 422


def test_operacion_requiere_sesion(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/tareas").status_code == 401
    assert (
        cliente.post("/api/v1/reportes", json={"nombre": "x", "finalidad": "y"}).status_code == 401
    )

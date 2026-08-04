from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dominios.operacion.modelos import EstadoTarea, PrioridadTarea, Tarea


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


def test_reporte_agrega_volumen_ficticio_sin_exponer_filas(
    cliente: TestClient, token_admin: str, sesion_db: Session
) -> None:
    ahora = datetime.now(UTC)
    sesion_db.add_all(
        [
            Tarea(
                titulo=f"Tarea ficticia {indice}",
                descripcion=None,
                prioridad=PrioridadTarea.MEDIA,
                estado=EstadoTarea.PENDIENTE if indice % 2 else EstadoTarea.COMPLETADA,
                vence_en=None,
                creada_por_id=None,
                responsable_id=None,
                paciente_id=None,
                estudio_id=None,
                creada_en=ahora,
                actualizada_en=ahora,
            )
            for indice in range(250)
        ]
    )
    sesion_db.commit()
    respuesta = cliente.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "nombre": "Volumen ficticio",
            "finalidad": "Prueba de agregación",
            "estados_tarea": ["pendiente"],
        },
    )
    assert respuesta.status_code == 201
    contenido = respuesta.json()["contenido"]
    assert contenido["metricas"]["tareas"]["valor"] == 125
    assert contenido["filtros"]["estados_tarea"] == ["pendiente"]
    assert "filas" not in contenido

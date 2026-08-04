from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.cupos.modelos import CupoDemo


def _crear_base(cliente: TestClient, token: str) -> tuple[dict[str, Any], dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    paciente = cliente.post(
        "/api/v1/pacientes-demo",
        headers=headers,
        json={
            "codigo": "PX-DEMO-CUPO-01",
            "rango_etario": "50–64 años",
            "patologia": "Ficticia",
        },
    ).json()
    estudio = cliente.post(
        "/api/v1/estudios",
        headers=headers,
        json={
            "codigo_interno": "EST-CUPO-DEMO",
            "titulo": "Cupos sintéticos",
            "patrocinador": "Demo",
            "fase": "Demo",
            "patologia": "Ficticia",
            "escenario_clinico": "Ficticio",
            "linea_tratamiento": "Ficticia",
        },
    ).json()
    return paciente, estudio


def test_cupo_confirma_reserva_ocupa_y_conserva_historial(
    cliente: TestClient, token_admin: str
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    paciente, estudio = _crear_base(cliente, token_admin)
    creada = cliente.post(
        "/api/v1/cupos-demo",
        headers=headers,
        json={
            "estudio_id": estudio["id"],
            "fuente": "Patrocinador ficticio",
            "motivo": "Confirmación demo",
        },
    )
    assert creada.status_code == 201
    assert creada.json()["estado"] == "confirmado"
    assert creada.json()["dias_validez"] == 30
    identificador = creada.json()["id"]
    reservada = cliente.patch(
        f"/api/v1/cupos-demo/{identificador}",
        headers=headers,
        json={"estado": "reservado", "paciente_id": paciente["id"], "motivo": "Reserva sintética"},
    )
    assert reservada.status_code == 200
    assert reservada.json()["paciente_id"] == paciente["id"]
    ocupada = cliente.patch(
        f"/api/v1/cupos-demo/{identificador}",
        headers=headers,
        json={"estado": "ocupado", "motivo": "Cupo utilizado en demo"},
    )
    assert ocupada.status_code == 200
    assert [h["estado_nuevo"] for h in ocupada.json()["historial"]] == [
        "confirmado",
        "reservado",
        "ocupado",
    ]


def test_vencimiento_no_reasigna_y_exige_reconfirmacion(
    cliente: TestClient, token_admin: str, sesion_db: Session
) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    paciente, estudio = _crear_base(cliente, token_admin)
    item = cliente.post(
        "/api/v1/cupos-demo",
        headers=headers,
        json={"estudio_id": estudio["id"], "fuente": "Correo ficticio", "motivo": "Demo"},
    ).json()
    cliente.patch(
        f"/api/v1/cupos-demo/{item['id']}",
        headers=headers,
        json={"estado": "reservado", "paciente_id": paciente["id"], "motivo": "Reserva demo"},
    )
    cupo = sesion_db.scalar(select(CupoDemo).where(CupoDemo.id == item["id"]))
    assert cupo is not None
    cupo.vence_en = datetime.now(UTC) - timedelta(minutes=1)
    sesion_db.commit()
    listado = cliente.get("/api/v1/cupos-demo", headers=headers).json()
    vencido = next(c for c in listado if c["id"] == item["id"])
    assert vencido["estado"] == "pendiente_reconfirmacion"
    assert vencido["paciente_id"] == paciente["id"]
    assert vencido["historial"][-1]["motivo"].startswith("Vigencia vencida")


def test_cupo_valida_vigencia_y_paciente(cliente: TestClient, token_admin: str) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    _, estudio = _crear_base(cliente, token_admin)
    invalida = cliente.post(
        "/api/v1/cupos-demo",
        headers=headers,
        json={"estudio_id": estudio["id"], "fuente": "Demo", "motivo": "Demo", "dias_validez": 7},
    )
    assert invalida.status_code == 422
    creada = cliente.post(
        "/api/v1/cupos-demo",
        headers=headers,
        json={"estudio_id": estudio["id"], "fuente": "Demo", "motivo": "Demo", "dias_validez": 90},
    ).json()
    respuesta = cliente.patch(
        f"/api/v1/cupos-demo/{creada['id']}",
        headers=headers,
        json={"estado": "reservado", "motivo": "Sin paciente"},
    )
    assert respuesta.status_code == 422

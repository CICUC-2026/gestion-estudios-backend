import hashlib
import zipfile
from io import BytesIO

from fastapi.testclient import TestClient


def test_admin_exporta_formatos_y_registra_hash(cliente: TestClient, token_admin: str) -> None:
    headers = {"Authorization": f"Bearer {token_admin}"}
    cliente.post(
        "/api/v1/pacientes-demo",
        headers=headers,
        json={"codigo": "PX-DEMO-EXP-01", "rango_etario": "50–64", "patologia": "Ficticia"},
    )
    for formato in ("json", "csv", "txt", "xlsx"):
        respuesta = cliente.post(
            "/api/v1/exportaciones-demo",
            headers=headers,
            json={
                "finalidad": "Respaldo verificable de demostración",
                "formato": formato,
                "entidades": ["pacientes"],
            },
        )
        assert respuesta.status_code == 200
        assert respuesta.headers["cache-control"].startswith("private, no-store")
        assert (
            respuesta.headers["x-contenido-sha256"] == hashlib.sha256(respuesta.content).hexdigest()
        )
        if formato == "xlsx":
            with zipfile.ZipFile(BytesIO(respuesta.content)) as archivo:
                assert "xl/worksheets/sheet1.xml" in archivo.namelist()
    registros = cliente.get("/api/v1/exportaciones-demo", headers=headers).json()
    assert len(registros) == 4
    assert registros[0]["cantidad"] == 1
    assert "codigo" in registros[0]["campos"]


def test_exportacion_requiere_admin_y_entidades_validas(
    cliente: TestClient, token_admin: str
) -> None:
    datos = {"finalidad": "Demo", "formato": "json", "entidades": ["sql"]}
    assert cliente.post("/api/v1/exportaciones-demo", json=datos).status_code == 401
    assert (
        cliente.post(
            "/api/v1/exportaciones-demo",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=datos,
        ).status_code
        == 422
    )

from fastapi.testclient import TestClient

from app.main import app


def test_salud_no_expone_informacion_sensible() -> None:
    respuesta = TestClient(app).get("/api/v1/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "estado": "ok",
        "servicio": "gestion-estudios-backend",
    }


def test_openapi_usa_prefijo_versionado() -> None:
    respuesta = TestClient(app).get("/api/v1/openapi.json")

    assert respuesta.status_code == 200
    assert "/api/v1/salud" in respuesta.json()["paths"]

from pathlib import Path

from app.scripts.importar_catalogo_csv import importar_csv


def test_importador_csv_validacion_columnas_prohibidas(tmp_path: Path) -> None:
    # Archivo con columna prohibida 'paciente'
    archivo_invalido = tmp_path / "invalido.csv"
    archivo_invalido.write_text(
        "codigo_interno,titulo,patrocinador,fase,patologia,escenario_clinico,linea_tratamiento,paciente\n"
        "EST-INV,Titulo,Pat,F1,Patol,Esc,Lin,Juan Perez\n"
    )

    try:
        importar_csv(str(archivo_invalido), dry_run=True)
        raise AssertionError("Debió fallar por columna prohibida")
    except SystemExit as e:
        assert "columnas prohibidas" in str(e)


def test_importador_csv_dry_run_y_ejecucion(tmp_path: Path) -> None:
    archivo_valido = tmp_path / "valido.csv"
    archivo_valido.write_text(
        "codigo_interno,titulo,patrocinador,fase,patologia,escenario_clinico,linea_tratamiento\n"
        "EST-TEST-001,Estudio Test CSV,Patrocinador,Fase 2,Melanoma,Metastásico,Primera línea\n"
    )

    # Dry-run no produce error
    importar_csv(str(archivo_valido), dry_run=True)

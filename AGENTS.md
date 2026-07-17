# AGENTS.md — Backend CICUC

Aplican las reglas maestras de `CICUC-2026/gestion-estudios-documentacion`.

- Confirmar que `origin` apunta a `CICUC-2026/gestion-estudios-backend`.
- No copiar código, configuración, secretos ni modelos de otros productos.
- Leer HU, feature, ADRs y matriz de regresión antes de editar.
- No inventar campos o reglas clínicas.
- FastAPI solo coordina HTTP; reglas viven en servicios de dominio/aplicación.
- Validar permisos en cada endpoint y probar denegaciones.
- Cambios de datos requieren migración, modelo, esquema, servicio y tests.
- No registrar datos sensibles en logs.
- No implementar IA ni elegibilidad automática en la primera versión.

Antes de cerrar: lint, tipos, Pytest, migraciones y prueba de API según alcance.

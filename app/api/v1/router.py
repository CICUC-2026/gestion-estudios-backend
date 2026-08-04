from fastapi import APIRouter

from app.api.v1.autenticacion import router as autenticacion_router
from app.api.v1.estudios import router as estudios_router
from app.api.v1.operacion import router as operacion_router
from app.api.v1.pacientes import router as pacientes_router
from app.api.v1.preseleccion import router as preseleccion_router
from app.api.v1.salud import router as salud_router
from app.api.v1.usuarios import router as usuarios_router

router = APIRouter()
router.include_router(salud_router, tags=["salud"])
router.include_router(autenticacion_router)
router.include_router(usuarios_router)
router.include_router(estudios_router)
router.include_router(operacion_router)
router.include_router(pacientes_router)
router.include_router(preseleccion_router)

import getpass

from email_validator import validate_email
from sqlalchemy import select

from app.base_datos.sesion import FabricaSesiones
from app.dominios.autenticacion.esquemas import CrearUsuario
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import crear_usuario, normalizar_correo


def main() -> None:
    correo = validate_email(
        input("Correo institucional: ").strip(), check_deliverability=False
    ).normalized
    nombres = input("Nombres: ").strip()
    apellidos = input("Apellidos: ").strip()
    contrasena = getpass.getpass("Contraseña inicial (mínimo 12 caracteres): ")
    with FabricaSesiones() as sesion_db:
        if sesion_db.scalar(select(Usuario).where(Usuario.correo == normalizar_correo(correo))):
            raise SystemExit("La cuenta ya existe.")
        usuario = crear_usuario(
            sesion_db,
            CrearUsuario(
                correo=correo,
                nombres=nombres,
                apellidos=apellidos,
                contrasena_inicial=contrasena,
                es_administrador_sistema=True,
            ),
            actor_id=None,
            direccion_ip=None,
        )
    print(f"Administrador creado: {usuario.correo}")


if __name__ == "__main__":
    main()

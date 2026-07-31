"""evolucion_inventario_operativo_hu30_hu32

Revision ID: 7d830a34b7e1
Revises: 9d634fbf4119
Create Date: 2026-07-31 15:21:59.939597
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7d830a34b7e1'
down_revision: str | None = '9d634fbf4119'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Crear Postgres Enums explícitamente antes de agregar columnas
    estado_op_cohorte = postgresql.ENUM('ACTIVADO', 'CERRADO_TEMPORALMENTE', 'CERRADO_DEFINITIVO', 'SUSPENDIDO', 'SIN_CONFIRMAR', name='estado_operacional_cohorte_enum')
    estado_op_cohorte.create(op.get_bind(), checkfirst=True)

    estado_disp_cohorte = postgresql.ENUM('CON_CUPO', 'SIN_CUPO', 'LISTA_ESPERA', 'SLOT_RESERVADO', 'SIN_CONFIRMAR', name='estado_disponibilidad_cohorte_enum')
    estado_disp_cohorte.create(op.get_bind(), checkfirst=True)

    alcance_crit = postgresql.ENUM('ESTUDIO', 'COHORTE', 'BRAZO', name='alcance_criterio_enum')
    alcance_crit.create(op.get_bind(), checkfirst=True)

    estado_op_estudio = postgresql.ENUM('ACTIVADO', 'CERRADO_TEMPORALMENTE', 'CERRADO_DEFINITIVO', 'SUSPENDIDO', 'SIN_CONFIRMAR', name='estado_operacional_estudio_enum')
    estado_op_estudio.create(op.get_bind(), checkfirst=True)

    estado_disp_estudio = postgresql.ENUM('CON_CUPO', 'SIN_CUPO', 'LISTA_ESPERA', 'SLOT_RESERVADO', 'SIN_CONFIRMAR', name='estado_disponibilidad_estudio_enum')
    estado_disp_estudio.create(op.get_bind(), checkfirst=True)

    # 2. Crear Tablas
    op.create_table('historial_estados_estudio',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('estudio_id', sa.Uuid(), nullable=False),
        sa.Column('campo_modificado', sa.String(length=64), nullable=False),
        sa.Column('valor_anterior', sa.String(length=64), nullable=True),
        sa.Column('valor_nuevo', sa.String(length=64), nullable=False),
        sa.Column('fecha', sa.DateTime(timezone=True), nullable=False),
        sa.Column('autor_id', sa.Uuid(), nullable=True),
        sa.Column('fuente', sa.String(length=256), nullable=True),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['autor_id'], ['usuarios.id'], name=op.f('fk_historial_estados_estudio_autor_id_usuarios'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['estudio_id'], ['estudios.id'], name=op.f('fk_historial_estados_estudio_estudio_id_estudios'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_historial_estados_estudio'))
    )
    op.create_index(op.f('ix_historial_estados_estudio_estudio_id'), 'historial_estados_estudio', ['estudio_id'], unique=False)

    op.create_table('brazos_estudio',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('cohorte_id', sa.Uuid(), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['cohorte_id'], ['cohortes_estudios.id'], name=op.f('fk_brazos_estudio_cohorte_id_cohortes_estudios'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_brazos_estudio'))
    )
    op.create_index(op.f('ix_brazos_estudio_cohorte_id'), 'brazos_estudio', ['cohorte_id'], unique=False)

    # 3. Columnas a cohortes_estudios
    op.add_column('cohortes_estudios', sa.Column('patologia', sa.String(length=120), nullable=True))
    op.add_column('cohortes_estudios', sa.Column('subtipo_histologico', sa.String(length=120), nullable=True))
    op.add_column('cohortes_estudios', sa.Column('escenario_clinico', sa.String(length=120), nullable=True))
    op.add_column('cohortes_estudios', sa.Column('linea_tratamiento', sa.String(length=64), nullable=True))
    op.add_column('cohortes_estudios', sa.Column('estado_operacional', sa.Enum('ACTIVADO', 'CERRADO_TEMPORALMENTE', 'CERRADO_DEFINITIVO', 'SUSPENDIDO', 'SIN_CONFIRMAR', name='estado_operacional_cohorte_enum'), nullable=True))
    op.add_column('cohortes_estudios', sa.Column('disponibilidad', sa.Enum('CON_CUPO', 'SIN_CUPO', 'LISTA_ESPERA', 'SLOT_RESERVADO', 'SIN_CONFIRMAR', name='estado_disponibilidad_cohorte_enum'), nullable=True))

    # 4. Columnas a criterios_manuales
    op.add_column('criterios_manuales', sa.Column('alcance', sa.Enum('ESTUDIO', 'COHORTE', 'BRAZO', name='alcance_criterio_enum'), server_default='ESTUDIO', nullable=False))
    op.add_column('criterios_manuales', sa.Column('cohorte_id', sa.Uuid(), nullable=True))
    op.add_column('criterios_manuales', sa.Column('brazo_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_criterios_manuales_alcance'), 'criterios_manuales', ['alcance'], unique=False)
    op.create_foreign_key(op.f('fk_criterios_manuales_brazo_id_brazos_estudio'), 'criterios_manuales', 'brazos_estudio', ['brazo_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_criterios_manuales_cohorte_id_cohortes_estudios'), 'criterios_manuales', 'cohortes_estudios', ['cohorte_id'], ['id'], ondelete='SET NULL')

    # 5. Columnas a estudios
    op.add_column('estudios', sa.Column('estado_operacional', sa.Enum('ACTIVADO', 'CERRADO_TEMPORALMENTE', 'CERRADO_DEFINITIVO', 'SUSPENDIDO', 'SIN_CONFIRMAR', name='estado_operacional_estudio_enum'), server_default='SIN_CONFIRMAR', nullable=False))
    op.add_column('estudios', sa.Column('disponibilidad', sa.Enum('CON_CUPO', 'SIN_CUPO', 'LISTA_ESPERA', 'SLOT_RESERVADO', 'SIN_CONFIRMAR', name='estado_disponibilidad_estudio_enum'), server_default='SIN_CONFIRMAR', nullable=False))
    op.add_column('estudios', sa.Column('fuente_informacion', sa.String(length=256), nullable=True))
    op.add_column('estudios', sa.Column('fecha_corte', sa.DateTime(timezone=True), nullable=True))
    op.add_column('estudios', sa.Column('verificado_por_id', sa.Uuid(), nullable=True))
    op.add_column('estudios', sa.Column('fecha_verificacion', sa.DateTime(timezone=True), nullable=True))
    op.add_column('estudios', sa.Column('proxima_revision', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_estudios_disponibilidad'), 'estudios', ['disponibilidad'], unique=False)
    op.create_index(op.f('ix_estudios_estado_operacional'), 'estudios', ['estado_operacional'], unique=False)
    op.create_foreign_key(op.f('fk_estudios_verificado_por_id_usuarios'), 'estudios', 'usuarios', ['verificado_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(op.f('fk_estudios_verificado_por_id_usuarios'), 'estudios', type_='foreignkey')
    op.drop_index(op.f('ix_estudios_estado_operacional'), table_name='estudios')
    op.drop_index(op.f('ix_estudios_disponibilidad'), table_name='estudios')
    op.drop_column('estudios', 'proxima_revision')
    op.drop_column('estudios', 'fecha_verificacion')
    op.drop_column('estudios', 'verificado_por_id')
    op.drop_column('estudios', 'fecha_corte')
    op.drop_column('estudios', 'fuente_informacion')
    op.drop_column('estudios', 'disponibilidad')
    op.drop_column('estudios', 'estado_operacional')
    op.drop_constraint(op.f('fk_criterios_manuales_cohorte_id_cohortes_estudios'), 'criterios_manuales', type_='foreignkey')
    op.drop_constraint(op.f('fk_criterios_manuales_brazo_id_brazos_estudio'), 'criterios_manuales', type_='foreignkey')
    op.drop_index(op.f('ix_criterios_manuales_alcance'), table_name='criterios_manuales')
    op.drop_column('criterios_manuales', 'brazo_id')
    op.drop_column('criterios_manuales', 'cohorte_id')
    op.drop_column('criterios_manuales', 'alcance')
    op.drop_column('cohortes_estudios', 'disponibilidad')
    op.drop_column('cohortes_estudios', 'estado_operacional')
    op.drop_column('cohortes_estudios', 'linea_tratamiento')
    op.drop_column('cohortes_estudios', 'escenario_clinico')
    op.drop_column('cohortes_estudios', 'subtipo_histologico')
    op.drop_column('cohortes_estudios', 'patologia')
    op.drop_table('brazos_estudio')
    op.drop_table('historial_estados_estudio')

    sa.Enum(name='estado_disponibilidad_estudio_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='estado_operacional_estudio_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='alcance_criterio_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='estado_disponibilidad_cohorte_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='estado_operacional_cohorte_enum').drop(op.get_bind(), checkfirst=True)

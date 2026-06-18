"""add tematica_id to paquete

Revision ID: 36186f70f7c9
Revises: 
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36186f70f7c9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('paquete', sa.Column('tematica_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_paquete_tematica_id',
        'paquete', 'tematica',
        ['tematica_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_paquete_tematica_id', 'paquete', type_='foreignkey')
    op.drop_column('paquete', 'tematica_id')

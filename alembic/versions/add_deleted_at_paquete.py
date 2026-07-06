"""add deleted_at to paquete

Revision ID: c1a2b3d4e5f6
Revises: b020bade6acb
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = 'b020bade6acb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('paquete', sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('paquete', 'deleted_at')
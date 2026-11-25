"""add source_anchor and target_anchor to mind_canvas_edges

Revision ID: 0007_mind_canvas_edges
Revises: 0006_mind
Create Date: 2026-11-25 12:31:04.235943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_mind_canvas_edges'
down_revision: Union[str, None] = '0006_mind'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # La tabla mind_canvas_edges ya existe pero le faltan source_anchor y target_anchor
    # SQLite no soporta ADD COLUMN IF NOT EXISTS, así que usamos batch_alter_table
    with op.batch_alter_table('mind_canvas_edges') as batch_op:
        batch_op.add_column(sa.Column('source_anchor', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('target_anchor', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('mind_canvas_edges') as batch_op:
        batch_op.drop_column('source_anchor')
        batch_op.drop_column('target_anchor')

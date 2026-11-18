"""Widget is_visible as Boolean

Revision ID: 0004_widget_boolean
Revises: 0003_dashboard_settings
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0004_widget_boolean"
down_revision: Union[str, None] = "0003_dashboard_settings"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # En SQLite, Boolean se almacena como INTEGER (0/1), por lo que no se
    # requiere ALTER TABLE. El cambio es solo en el modelo de SQLAlchemy para
    # devolver Python bool en lugar de int al leer.
    pass


def downgrade() -> None:
    pass
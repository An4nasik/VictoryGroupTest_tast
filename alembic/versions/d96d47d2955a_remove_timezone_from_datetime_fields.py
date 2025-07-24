"""remove_timezone_from_datetime_fields
Revision ID: d96d47d2955a
Revises: 8eecb0c276e3
Create Date: 2025-07-24 19:18:58.305030
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = 'd96d47d2955a'
down_revision: Union[str, Sequence[str], None] = '8eecb0c276e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    """Upgrade schema."""
    pass
def downgrade() -> None:
    """Downgrade schema."""
    pass

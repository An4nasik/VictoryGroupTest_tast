"""Initial migration with proper enums
Revision ID: 112674ddae17
Revises: 
Create Date: 2025-07-24 18:00:54.955771
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = '112674ddae17'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    """Upgrade schema."""
    pass
def downgrade() -> None:
    """Downgrade schema."""
    pass

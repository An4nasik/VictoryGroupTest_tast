"""add_multimedia_support_with_default
Revision ID: ec86a99ea14f
Revises: d96d47d2955a
Create Date: 2025-07-24 22:48:20.850922
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = 'ec86a99ea14f'
down_revision: Union[str, Sequence[str], None] = 'd96d47d2955a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('newsletters', sa.Column('content_type', postgresql.ENUM('TEXT', 'PHOTO', 'VIDEO', 'ANIMATION', 'DOCUMENT', name='contenttypeenum'), server_default='TEXT', nullable=False))
def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('newsletters', 'content_type')

"""remove_timezone_from_datetime_fields
Revision ID: 8eecb0c276e3
Revises: 112674ddae17
Create Date: 2025-07-24 19:18:15.628693
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = '8eecb0c276e3'
down_revision: Union[str, Sequence[str], None] = '112674ddae17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('newsletters', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('newsletters', 'scheduled_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True)
def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('newsletters', 'scheduled_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    op.alter_column('newsletters', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False,
               existing_server_default=sa.text('now()'))

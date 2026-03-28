"""add last_polled_at to devices

Revision ID: h3c4d5e6f7a8
Revises: g2b3c4d5e6f7
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa

revision = 'h3c4d5e6f7a8'
down_revision = 'g2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('devices', sa.Column('last_polled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('devices', 'last_polled_at')

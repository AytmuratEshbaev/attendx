"""add picture_url to attendance_logs

Revision ID: g2b3c4d5e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'g2b3c4d5e6f7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('attendance_logs', sa.Column('picture_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('attendance_logs', 'picture_url')

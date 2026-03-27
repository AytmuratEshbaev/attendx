"""add categories table and category_id to students

Revision ID: b3f1a2c4d5e6
Revises: 9064db9409c9
Create Date: 2026-02-20 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3f1a2c4d5e6"
down_revision: Union[str, None] = "9064db9409c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])

    op.add_column(
        "students",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_students_category_id",
        "students",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_students_category_id", "students", ["category_id"])

    # Widen class_name column to 100 chars (was 50)
    op.alter_column("students", "class_name", type_=sa.String(100), existing_nullable=True)


def downgrade() -> None:
    op.drop_index("ix_students_category_id", "students")
    op.drop_constraint("fk_students_category_id", "students", type_="foreignkey")
    op.drop_column("students", "category_id")
    op.drop_index("ix_categories_name", "categories")
    op.drop_table("categories")

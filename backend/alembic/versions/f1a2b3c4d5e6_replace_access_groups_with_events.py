"""replace_access_groups_with_events

Revision ID: f1a2b3c4d5e6
Revises: a0dac80a0bcd
Create Date: 2026-02-25 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "a0dac80a0bcd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old access_group tables
    op.drop_index(
        "ix_access_group_students_student_id",
        table_name="access_group_students",
        if_exists=True,
    )
    op.drop_index(
        "ix_access_group_students_access_group_id",
        table_name="access_group_students",
        if_exists=True,
    )
    op.drop_table("access_group_students")
    op.drop_table("access_group_devices")
    op.drop_table("access_groups")

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("weekdays", sa.Text(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("ot_start_time", sa.Time(), nullable=True),
        sa.Column("ot_end_time", sa.Time(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create event_devices junction table
    op.create_table(
        "event_devices",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("event_id", "device_id"),
    )

    # Create event_students table
    op.create_table(
        "event_students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("sync_status", sa.String(length=20), nullable=False),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "student_id", name="uq_event_student"),
    )
    op.create_index(
        op.f("ix_event_students_event_id"), "event_students", ["event_id"], unique=False
    )
    op.create_index(
        op.f("ix_event_students_student_id"),
        "event_students",
        ["student_id"],
        unique=False,
    )

    # Create event_device_plan_templates table
    op.create_table(
        "event_device_plan_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("plan_template_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id", "device_id", name="uq_event_device_template"
        ),
    )
    op.create_index(
        op.f("ix_event_device_plan_templates_event_id"),
        "event_device_plan_templates",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_device_plan_templates_device_id"),
        "event_device_plan_templates",
        ["device_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_event_device_plan_templates_device_id"),
        table_name="event_device_plan_templates",
    )
    op.drop_index(
        op.f("ix_event_device_plan_templates_event_id"),
        table_name="event_device_plan_templates",
    )
    op.drop_table("event_device_plan_templates")
    op.drop_index(
        op.f("ix_event_students_student_id"), table_name="event_students"
    )
    op.drop_index(
        op.f("ix_event_students_event_id"), table_name="event_students"
    )
    op.drop_table("event_students")
    op.drop_table("event_devices")
    op.drop_table("events")

    # Recreate access_group tables
    op.create_table(
        "access_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "access_group_devices",
        sa.Column("access_group_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["access_group_id"], ["access_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("access_group_id", "device_id"),
    )
    op.create_table(
        "access_group_students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("access_group_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("sync_status", sa.String(length=20), nullable=False),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["access_group_id"], ["access_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "access_group_id", "student_id", name="uq_access_group_student"
        ),
    )
    op.create_index(
        op.f("ix_access_group_students_access_group_id"),
        "access_group_students",
        ["access_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_group_students_student_id"),
        "access_group_students",
        ["student_id"],
        unique=False,
    )

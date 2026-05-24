"""add service_orders and service_history

Adds the service workflow tables used by the Service Technician panel:

* ``service_orders`` — scheduled/in-progress/completed maintenance work
  for a vehicle, owned by a technician.
* ``service_history`` — records of actually executed work tied to a
  service order (notes, parts replaced, mileage at the time).

Both tables cascade on the parent ``vehicle`` delete, and history
cascades on the parent ``service_order`` delete.

Revision ID: i0d1e2f3a4b5
Revises: h9c0d1e2f3a4
Create Date: 2026-05-10 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i0d1e2f3a4b5"
down_revision: str | Sequence[str] | None = "h9c0d1e2f3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. service_orders
    # -------------------------------------------------------------------------
    op.create_table(
        "service_orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
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
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technician_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name="fk_service_orders_vehicle_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["technician_id"],
            ["users.id"],
            name="fk_service_orders_technician_id",
        ),
        sa.CheckConstraint(
            "cost IS NULL OR cost >= 0",
            name="ck_service_order_cost_non_negative",
        ),
    )
    op.create_index("ix_service_orders_vehicle_id", "service_orders", ["vehicle_id"])
    op.create_index("ix_service_orders_technician_id", "service_orders", ["technician_id"])
    op.create_index("ix_service_orders_status", "service_orders", ["status"])
    op.create_index("ix_service_orders_scheduled_date", "service_orders", ["scheduled_date"])
    op.create_index("ix_service_orders_type", "service_orders", ["type"])

    # -------------------------------------------------------------------------
    # 2. service_history
    # -------------------------------------------------------------------------
    op.create_table(
        "service_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
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
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("service_order_id", sa.Uuid(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "parts_replaced",
            ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("mileage_at_service", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name="fk_service_history_vehicle_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["service_order_id"],
            ["service_orders.id"],
            name="fk_service_history_service_order_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "mileage_at_service >= 0",
            name="ck_service_history_mileage_non_negative",
        ),
    )
    op.create_index("ix_service_history_vehicle_id", "service_history", ["vehicle_id"])
    op.create_index(
        "ix_service_history_service_order_id",
        "service_history",
        ["service_order_id"],
    )


def downgrade() -> None:
    # service_history first (FK depends on service_orders)
    op.drop_index("ix_service_history_service_order_id", table_name="service_history")
    op.drop_index("ix_service_history_vehicle_id", table_name="service_history")
    op.drop_table("service_history")

    # service_orders
    op.drop_index("ix_service_orders_type", table_name="service_orders")
    op.drop_index("ix_service_orders_scheduled_date", table_name="service_orders")
    op.drop_index("ix_service_orders_status", table_name="service_orders")
    op.drop_index("ix_service_orders_technician_id", table_name="service_orders")
    op.drop_index("ix_service_orders_vehicle_id", table_name="service_orders")
    op.drop_table("service_orders")

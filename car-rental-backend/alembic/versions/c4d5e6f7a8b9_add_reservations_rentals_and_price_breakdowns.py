"""add reservations, rentals (active), and rental_price_breakdowns

Rename old rentals table -> reservations (adds CONFIRMED status, drops notes).
Create new rentals table for active rentals linked to reservations.
Create rental_price_breakdowns table.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-06 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Rename rentals -> reservations
    # -------------------------------------------------------------------------
    op.rename_table("rentals", "reservations")

    # Rename existing indexes to reflect new table name
    op.execute("ALTER INDEX IF EXISTS ix_rentals_user_id RENAME TO ix_reservations_user_id")
    op.execute("ALTER INDEX IF EXISTS ix_rentals_vehicle_id RENAME TO ix_reservations_vehicle_id")

    # Add status index (was not present on old table)
    op.create_index("ix_reservations_status", "reservations", ["status"])

    # Drop notes column (not part of Reservation model)
    op.drop_column("reservations", "notes")

    # -------------------------------------------------------------------------
    # 2. Create new rentals table (active rental linked 1:1 to reservation)
    # -------------------------------------------------------------------------
    op.create_table(
        "rentals",
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
        sa.Column("reservation_id", sa.Uuid(), nullable=False),
        sa.Column("pickup_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("return_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mileage_start", sa.Integer(), nullable=False),
        sa.Column("mileage_end", sa.Integer(), nullable=True),
        sa.Column("fuel_level_start", sa.Numeric(5, 2), nullable=False),
        sa.Column("fuel_level_end", sa.Numeric(5, 2), nullable=True),
        sa.Column("damage_notes", sa.Text(), nullable=True),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reservation_id"], ["reservations.id"], name="fk_rentals_reservation_id"
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], name="fk_rentals_employee_id"),
        sa.UniqueConstraint("reservation_id", name="uq_rentals_reservation_id"),
        sa.CheckConstraint("mileage_start >= 0", name="ck_rental_mileage_start_non_negative"),
        sa.CheckConstraint(
            "mileage_end IS NULL OR mileage_end >= mileage_start",
            name="ck_rental_mileage_end_gte_start",
        ),
        sa.CheckConstraint(
            "fuel_level_start >= 0 AND fuel_level_start <= 100",
            name="ck_rental_fuel_level_start_range",
        ),
        sa.CheckConstraint(
            "fuel_level_end IS NULL OR (fuel_level_end >= 0 AND fuel_level_end <= 100)",
            name="ck_rental_fuel_level_end_range",
        ),
        sa.CheckConstraint(
            "return_date IS NULL OR return_date > pickup_date",
            name="ck_rental_return_after_pickup",
        ),
    )
    op.create_index("ix_rentals_employee_id", "rentals", ["employee_id"])

    # -------------------------------------------------------------------------
    # 3. Create rental_price_breakdowns table (linked 1:1 to rentals)
    # -------------------------------------------------------------------------
    op.create_table(
        "rental_price_breakdowns",
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
        sa.Column("rental_id", sa.Uuid(), nullable=False),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("fuel_surcharge", sa.Numeric(10, 2), nullable=False),
        sa.Column("risk_multiplier", sa.Numeric(6, 4), nullable=False),
        sa.Column("final_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["rental_id"], ["rentals.id"], name="fk_rental_price_breakdowns_rental_id"
        ),
        sa.UniqueConstraint("rental_id", name="uq_rental_price_breakdowns_rental_id"),
        sa.CheckConstraint("base_price >= 0", name="ck_price_breakdown_base_price_non_negative"),
        sa.CheckConstraint(
            "fuel_surcharge >= 0", name="ck_price_breakdown_fuel_surcharge_non_negative"
        ),
        sa.CheckConstraint(
            "risk_multiplier >= 1", name="ck_price_breakdown_risk_multiplier_gte_one"
        ),
        sa.CheckConstraint("final_price >= 0", name="ck_price_breakdown_final_price_non_negative"),
    )


def downgrade() -> None:
    # -------------------------------------------------------------------------
    # 3. Drop rental_price_breakdowns
    # -------------------------------------------------------------------------
    op.drop_table("rental_price_breakdowns")

    # -------------------------------------------------------------------------
    # 2. Drop new rentals table
    # -------------------------------------------------------------------------
    op.drop_index("ix_rentals_employee_id", "rentals")
    op.drop_table("rentals")

    # -------------------------------------------------------------------------
    # 1. Revert reservations -> rentals
    # -------------------------------------------------------------------------
    op.add_column("reservations", sa.Column("notes", sa.Text(), nullable=True))

    op.drop_index("ix_reservations_status", "reservations")
    op.execute("ALTER INDEX IF EXISTS ix_reservations_user_id RENAME TO ix_rentals_user_id")
    op.execute("ALTER INDEX IF EXISTS ix_reservations_vehicle_id RENAME TO ix_rentals_vehicle_id")

    op.rename_table("reservations", "rentals")

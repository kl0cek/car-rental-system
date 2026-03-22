"""add categories table and update vehicles

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Create categories table ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(20), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "price_multiplier",
            sa.Numeric(5, 3),
            nullable=False,
            server_default=sa.text("1.000"),
        ),
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
    )

    # --- Insert a default category so existing vehicles can reference it ---
    op.execute(
        "INSERT INTO categories (id, name, description, price_multiplier) "
        "VALUES ('00000000-0000-0000-0000-000000000001', 'economy', "
        "'Default category for existing vehicles', 1.000)"
    )

    # --- Add new columns to vehicles as NULLABLE first ---
    op.add_column("vehicles", sa.Column("vin", sa.String(17), nullable=True))
    op.add_column("vehicles", sa.Column("horsepower", sa.Integer(), nullable=True))
    op.add_column("vehicles", sa.Column("trunk_capacity", sa.Integer(), nullable=True))
    op.add_column(
        "vehicles",
        sa.Column("daily_base_price", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column("category_id", sa.Uuid(), nullable=True),
    )

    # --- Backfill existing rows ---
    # Copy daily_rate to daily_base_price if column exists
    op.execute(
        "UPDATE vehicles SET daily_base_price = daily_rate "
        "WHERE daily_base_price IS NULL AND EXISTS ("
        "  SELECT 1 FROM information_schema.columns "
        "  WHERE table_name = 'vehicles' AND column_name = 'daily_rate'"
        ")"
    )
    # Fallback if daily_rate doesn't exist
    op.execute("UPDATE vehicles SET daily_base_price = 0 WHERE daily_base_price IS NULL")

    op.execute(
        "UPDATE vehicles SET vin = 'UNKNOWN' || LPAD(CAST(ROW_NUMBER() OVER () AS TEXT), 10, '0') "
        "WHERE vin IS NULL"
    )
    op.execute("UPDATE vehicles SET horsepower = 100 WHERE horsepower IS NULL")
    op.execute("UPDATE vehicles SET trunk_capacity = 0 WHERE trunk_capacity IS NULL")
    op.execute(
        "UPDATE vehicles SET category_id = '00000000-0000-0000-0000-000000000001' "
        "WHERE category_id IS NULL"
    )

    # --- Set NOT NULL constraints ---
    op.alter_column("vehicles", "vin", nullable=False)
    op.alter_column("vehicles", "horsepower", nullable=False)
    op.alter_column("vehicles", "trunk_capacity", nullable=False)
    op.alter_column("vehicles", "daily_base_price", nullable=False)
    op.alter_column("vehicles", "category_id", nullable=False)

    # --- Add indexes, unique constraints, check constraints ---
    op.create_unique_constraint("uq_vehicles_vin", "vehicles", ["vin"])
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"])
    op.create_index("ix_vehicles_brand", "vehicles", ["brand"])
    op.create_index("ix_vehicles_engine_type", "vehicles", ["engine_type"])
    op.create_index("ix_vehicles_daily_base_price", "vehicles", ["daily_base_price"])
    op.create_index("ix_vehicles_status", "vehicles", ["status"])
    op.create_index("ix_vehicles_category_id", "vehicles", ["category_id"])

    op.create_foreign_key(
        "fk_vehicles_category_id",
        "vehicles",
        "categories",
        ["category_id"],
        ["id"],
    )

    op.create_check_constraint("ck_vehicle_horsepower_positive", "vehicles", "horsepower > 0")
    op.create_check_constraint("ck_vehicle_seats_positive", "vehicles", "seats > 0")
    op.create_check_constraint(
        "ck_vehicle_trunk_capacity_non_negative", "vehicles", "trunk_capacity >= 0"
    )

    # --- Drop old daily_rate column if it exists ---
    try:
        op.drop_column("vehicles", "daily_rate")
    except Exception:
        pass


def downgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column("daily_rate", sa.Numeric(10, 2), nullable=True),
    )
    op.execute("UPDATE vehicles SET daily_rate = daily_base_price")

    op.drop_constraint("ck_vehicle_trunk_capacity_non_negative", "vehicles", type_="check")
    op.drop_constraint("ck_vehicle_seats_positive", "vehicles", type_="check")
    op.drop_constraint("ck_vehicle_horsepower_positive", "vehicles", type_="check")
    op.drop_constraint("fk_vehicles_category_id", "vehicles", type_="foreignkey")

    op.drop_index("ix_vehicles_category_id", "vehicles")
    op.drop_index("ix_vehicles_status", "vehicles")
    op.drop_index("ix_vehicles_daily_base_price", "vehicles")
    op.drop_index("ix_vehicles_engine_type", "vehicles")
    op.drop_index("ix_vehicles_brand", "vehicles")
    op.drop_index("ix_vehicles_vin", "vehicles")
    op.drop_constraint("uq_vehicles_vin", "vehicles", type_="unique")

    op.drop_column("vehicles", "category_id")
    op.drop_column("vehicles", "daily_base_price")
    op.drop_column("vehicles", "trunk_capacity")
    op.drop_column("vehicles", "horsepower")
    op.drop_column("vehicles", "vin")

    op.drop_table("categories")

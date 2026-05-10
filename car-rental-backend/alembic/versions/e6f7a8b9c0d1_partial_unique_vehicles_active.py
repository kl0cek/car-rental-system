"""replace vin/license_plate unconditional unique with partial unique on is_active

Soft-deleted rows must not block re-onboarding the same physical car. Switch the
unique constraints on ``vehicles.vin`` and ``vehicles.license_plate`` to partial
unique indexes scoped to ``is_active = true``.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-05-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_unique_on_column(table: str, column: str) -> None:
    # Resolve the actual unique constraint name for the given column. Some
    # environments named it explicitly (e.g. `uq_vehicles_vin`), others got the
    # SQLAlchemy auto-name (`vehicles_vin_key`) when bootstrapped via
    # `Base.metadata.create_all`. Look it up at runtime so the migration runs
    # cleanly in either case.
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.table_schema = ccu.table_schema
            WHERE tc.table_name = :table
              AND ccu.column_name = :column
              AND tc.constraint_type = 'UNIQUE'
            """
        ),
        {"table": table, "column": column},
    )
    for (name,) in result:
        op.drop_constraint(name, table, type_="unique")


def upgrade() -> None:
    # Drop the existing unconditional unique constraints (name varies by env).
    _drop_unique_on_column("vehicles", "vin")
    _drop_unique_on_column("vehicles", "license_plate")

    # Create partial unique indexes — uniqueness is enforced only for active rows.
    op.create_index(
        "uq_vehicles_vin_active",
        "vehicles",
        ["vin"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index(
        "uq_vehicles_license_plate_active",
        "vehicles",
        ["license_plate"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_vehicles_license_plate_active", table_name="vehicles")
    op.drop_index("uq_vehicles_vin_active", table_name="vehicles")

    op.create_unique_constraint("vehicles_license_plate_key", "vehicles", ["license_plate"])
    op.create_unique_constraint("uq_vehicles_vin", "vehicles", ["vin"])

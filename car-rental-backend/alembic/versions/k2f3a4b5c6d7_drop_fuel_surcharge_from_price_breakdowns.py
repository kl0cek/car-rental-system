"""drop fuel_surcharge from rental_price_breakdowns

The pricing model no longer treats fuel as a price input. Final price is
``base_price * risk_multiplier`` where ``base_price`` already folds the
category multiplier and number of rented days. Drop the column and its
non-negative check constraint accordingly.

Revision ID: k2f3a4b5c6d7
Revises: j1e2f3a4b5c6
Create Date: 2026-05-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "k2f3a4b5c6d7"
down_revision: str | Sequence[str] | None = "j1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_price_breakdown_fuel_surcharge_non_negative",
        "rental_price_breakdowns",
        type_="check",
    )
    op.drop_column("rental_price_breakdowns", "fuel_surcharge")


def downgrade() -> None:
    op.add_column(
        "rental_price_breakdowns",
        sa.Column(
            "fuel_surcharge",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("rental_price_breakdowns", "fuel_surcharge", server_default=None)
    op.create_check_constraint(
        "ck_price_breakdown_fuel_surcharge_non_negative",
        "rental_price_breakdowns",
        "fuel_surcharge >= 0",
    )

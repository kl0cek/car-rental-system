"""rename incident severity values and add cost column

Renames ``IncidentSeverity`` values from ``low/medium/high`` to
``minor/moderate/major`` and adds an optional ``cost`` column on
``incidents`` with a non-negative check constraint.

Also relaxes the ``rental_price_breakdowns.risk_multiplier`` check
constraint to ``>= 0`` so the new piecewise multiplier scheme — which
allows values below 1.0 for low-risk/loyal customers (0.8, 0.9) — does
not violate it.

Note: ``downgrade()`` is lossy — the ``cost`` column is dropped, so any
data written into it after the upgrade is destroyed on rollback.

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-05-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h9c0d1e2f3a4"
down_revision: str | Sequence[str] | None = "g8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add cost column (nullable) with non-negative CheckConstraint
    op.add_column(
        "incidents",
        sa.Column("cost", sa.Numeric(10, 2), nullable=True),
    )
    op.create_check_constraint(
        "ck_incident_cost_non_negative",
        "incidents",
        "cost IS NULL OR cost >= 0",
    )

    # 2. Severity-value swap (low/medium/high → minor/moderate/major).
    #
    # The preceding migration (g8b9c0d1e2f3) created ``incidents.severity`` as
    # a plain VARCHAR(20), NOT as ``sa.Enum(..., native_enum=False)``. No CHECK
    # constraint was emitted on the column — verified by inspecting the live
    # schema (``\d+ incidents``: only ``ck_incident_cost_non_negative`` is
    # present). So there is no old CHECK to drop.
    #
    # We deliberately do NOT add a new CHECK either: SQLAlchemy ``StrEnum`` with
    # ``native_enum=False`` stores ``.name`` (uppercase) by default, so the
    # stored values would be ``MINOR/MODERATE/MAJOR`` — which wouldn't match a
    # lowercase CHECK and would reject every row inserted by the ORM. Value
    # enforcement happens at the application layer (Pydantic + the StrEnum
    # itself); the column stays as plain VARCHAR.
    op.execute(
        sa.text(
            """
            UPDATE incidents
            SET severity = CASE severity
                WHEN 'low' THEN 'minor'
                WHEN 'medium' THEN 'moderate'
                WHEN 'high' THEN 'major'
                ELSE severity
            END
            """
        )
    )

    # 3. Relax risk_multiplier lower bound: the new piecewise mapping allows
    #    0.8 and 0.9 for low-risk users, so the old "risk_multiplier >= 1"
    #    constraint would block inserts. Keep it non-negative instead.
    op.drop_constraint(
        "ck_price_breakdown_risk_multiplier_gte_one",
        "rental_price_breakdowns",
        type_="check",
    )
    op.create_check_constraint(
        "ck_price_breakdown_risk_multiplier_non_negative",
        "rental_price_breakdowns",
        "risk_multiplier >= 0",
    )


def downgrade() -> None:
    # Reverse the multiplier constraint change.
    op.drop_constraint(
        "ck_price_breakdown_risk_multiplier_non_negative",
        "rental_price_breakdowns",
        type_="check",
    )
    op.create_check_constraint(
        "ck_price_breakdown_risk_multiplier_gte_one",
        "rental_price_breakdowns",
        "risk_multiplier >= 1",
    )

    # Reverse the severity rename: minor → low, moderate → medium, major → high.
    # (No CHECK was added in upgrade(), so nothing to drop here.)
    op.execute(
        sa.text(
            """
            UPDATE incidents
            SET severity = CASE severity
                WHEN 'minor' THEN 'low'
                WHEN 'moderate' THEN 'medium'
                WHEN 'major' THEN 'high'
                ELSE severity
            END
            """
        )
    )

    # Drop the cost CheckConstraint and column. Lossy: any data written into
    # ``cost`` after the upgrade is destroyed here.
    op.drop_constraint("ck_incident_cost_non_negative", "incidents", type_="check")
    op.drop_column("incidents", "cost")

"""add avatar_url, risk_score and last_login_at to users

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-20 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "risk_score",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_user_risk_score_range",
        "users",
        "risk_score >= 0 AND risk_score <= 100",
    )
    # Indexes supporting GET /admin/users filters and sorts.
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_risk_score", "users", ["risk_score"])
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])
    # Indexes supporting GET /admin/reservations date-range sorts / overlap filter.
    op.create_index("ix_reservations_start_date", "reservations", ["start_date"])
    op.create_index("ix_reservations_end_date", "reservations", ["end_date"])


def downgrade() -> None:
    op.drop_index("ix_reservations_end_date", "reservations")
    op.drop_index("ix_reservations_start_date", "reservations")
    op.drop_index("ix_users_last_login_at", "users")
    op.drop_index("ix_users_risk_score", "users")
    op.drop_index("ix_users_role", "users")
    op.drop_constraint("ck_user_risk_score_range", "users", type_="check")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "risk_score")
    op.drop_column("users", "avatar_url")

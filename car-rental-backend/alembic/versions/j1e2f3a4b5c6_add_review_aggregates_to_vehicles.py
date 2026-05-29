"""add review aggregates to vehicles

Adds the denormalised columns used by the review system:

* ``avg_rating`` (Numeric(3,2), nullable) — average of all review ratings
  for the vehicle. ``NULL`` when no reviews exist (distinguishable from
  a literal 0.00 average).
* ``ratings_count`` (Integer, default 0) — number of reviews.

Both columns are maintained from application code (see
``app/services/review_service.py``) after MongoDB writes succeed. Reviews
themselves live in the ``reviews`` MongoDB collection — there is no SQL
table for them. The compound uniqueness constraint and rating range
check are enforced as a MongoDB unique index + ``$jsonSchema`` validator
created at startup by ``review_service.ensure_review_collection``.

Revision ID: j1e2f3a4b5c6
Revises: i0d1e2f3a4b5
Create Date: 2026-05-24 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "j1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "i0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column("avg_rating", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "ratings_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "ck_vehicle_avg_rating_range",
        "vehicles",
        "avg_rating IS NULL OR (avg_rating >= 1 AND avg_rating <= 5)",
    )
    op.create_check_constraint(
        "ck_vehicle_ratings_count_non_negative",
        "vehicles",
        "ratings_count >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_vehicle_ratings_count_non_negative", "vehicles", type_="check")
    op.drop_constraint("ck_vehicle_avg_rating_range", "vehicles", type_="check")
    op.drop_column("vehicles", "ratings_count")
    op.drop_column("vehicles", "avg_rating")

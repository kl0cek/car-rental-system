"""add vehicle_images, incidents, customer_notes; migrate vehicle.image_url

Splits the legacy single ``vehicles.image_url`` into a 1:N ``vehicle_images``
table, backfilling existing URLs as the primary image. Adds ``incidents``
(staff-recorded incidents tied to a customer and optionally a rental) and
``customer_notes`` (free-text staff annotations on a customer).

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-07 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. vehicle_images
    # -------------------------------------------------------------------------
    op.create_table(
        "vehicle_images",
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
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name="fk_vehicle_images_vehicle_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_vehicle_images_vehicle_id", "vehicle_images", ["vehicle_id"])
    op.create_index(
        "ix_vehicle_images_vehicle_id_position",
        "vehicle_images",
        ["vehicle_id", "position"],
    )
    op.create_index(
        "uq_vehicle_images_one_primary_per_vehicle",
        "vehicle_images",
        ["vehicle_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
    )

    # Backfill existing image_url into vehicle_images (one primary per vehicle)
    op.execute(
        sa.text(
            """
            INSERT INTO vehicle_images
                (id, created_at, updated_at, vehicle_id, url, position, is_primary)
            SELECT gen_random_uuid(), NOW(), NOW(), id, image_url, 0, true
            FROM vehicles
            WHERE image_url IS NOT NULL AND image_url <> ''
            """
        )
    )

    # Drop the legacy single-image column from vehicles
    op.drop_column("vehicles", "image_url")

    # -------------------------------------------------------------------------
    # 2. incidents
    # -------------------------------------------------------------------------
    op.create_table(
        "incidents",
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
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("rental_id", sa.Uuid(), nullable=True),
        sa.Column("reported_by_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["users.id"], name="fk_incidents_customer_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["rental_id"], ["rentals.id"], name="fk_incidents_rental_id", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["reported_by_id"], ["users.id"], name="fk_incidents_reported_by_id"
        ),
    )
    op.create_index("ix_incidents_customer_id", "incidents", ["customer_id"])
    op.create_index("ix_incidents_rental_id", "incidents", ["rental_id"])
    op.create_index("ix_incidents_reported_by_id", "incidents", ["reported_by_id"])
    op.create_index("ix_incidents_type", "incidents", ["type"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])

    # -------------------------------------------------------------------------
    # 3. customer_notes
    # -------------------------------------------------------------------------
    op.create_table(
        "customer_notes",
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
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["users.id"],
            name="fk_customer_notes_customer_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name="fk_customer_notes_author_id"
        ),
    )
    op.create_index("ix_customer_notes_customer_id", "customer_notes", ["customer_id"])
    op.create_index("ix_customer_notes_author_id", "customer_notes", ["author_id"])


def downgrade() -> None:
    # customer_notes
    op.drop_index("ix_customer_notes_author_id", table_name="customer_notes")
    op.drop_index("ix_customer_notes_customer_id", table_name="customer_notes")
    op.drop_table("customer_notes")

    # incidents
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_index("ix_incidents_type", table_name="incidents")
    op.drop_index("ix_incidents_reported_by_id", table_name="incidents")
    op.drop_index("ix_incidents_rental_id", table_name="incidents")
    op.drop_index("ix_incidents_customer_id", table_name="incidents")
    op.drop_table("incidents")

    # vehicle_images — restore image_url column from primary image, then drop
    op.add_column("vehicles", sa.Column("image_url", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE vehicles v
            SET image_url = vi.url
            FROM vehicle_images vi
            WHERE vi.vehicle_id = v.id AND vi.is_primary = true
            """
        )
    )
    op.drop_index(
        "uq_vehicle_images_one_primary_per_vehicle",
        table_name="vehicle_images",
    )
    op.drop_index("ix_vehicle_images_vehicle_id_position", table_name="vehicle_images")
    op.drop_index("ix_vehicle_images_vehicle_id", table_name="vehicle_images")
    op.drop_table("vehicle_images")

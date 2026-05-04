"""normalize vehicles.color to enum keys

Existing values were stored as Polish display strings (``Biały``, ``Czarny``, …).
Map them to stable English enum keys so the API can stay language-agnostic and
the frontend can resolve the localized label via i18n.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-05-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Mapping of legacy labels (Polish + a few English variants) to enum names.
# Lower-cased at compare time so capitalisation drift in seed data
# doesn't leak rows. Stored values are the enum *names* (uppercase) to
# match how SQLAlchemy's ``Enum(..., native_enum=False)`` persists the
# other StrEnum columns (engine_type, status, …).
_LEGACY_TO_NAME = {
    "biały": "WHITE",
    "czarny": "BLACK",
    "szary": "GREY",
    "srebrny": "SILVER",
    "niebieski": "BLUE",
    "czerwony": "RED",
    "zielony": "GREEN",
    "żółty": "YELLOW",
    "pomarańczowy": "ORANGE",
    "brązowy": "BROWN",
    "beżowy": "BEIGE",
    "white": "WHITE",
    "black": "BLACK",
    "grey": "GREY",
    "gray": "GREY",
    "silver": "SILVER",
    "blue": "BLUE",
    "red": "RED",
    "green": "GREEN",
    "yellow": "YELLOW",
    "orange": "ORANGE",
    "brown": "BROWN",
    "beige": "BEIGE",
}

_VALID_NAMES = (
    "WHITE",
    "BLACK",
    "GREY",
    "SILVER",
    "BLUE",
    "RED",
    "GREEN",
    "YELLOW",
    "ORANGE",
    "BROWN",
    "BEIGE",
    "OTHER",
)


def upgrade() -> None:
    for legacy, name in _LEGACY_TO_NAME.items():
        op.execute(
            sa.text("UPDATE vehicles SET color = :name WHERE LOWER(color) = :legacy").bindparams(
                name=name, legacy=legacy
            )
        )
    op.execute(
        sa.text("UPDATE vehicles SET color = 'OTHER' WHERE color NOT IN :names").bindparams(
            sa.bindparam("names", _VALID_NAMES, expanding=True)
        )
    )

    op.alter_column("vehicles", "color", type_=sa.String(20), existing_nullable=False)
    op.create_index("ix_vehicles_color", "vehicles", ["color"])


def downgrade() -> None:
    op.drop_index("ix_vehicles_color", table_name="vehicles")
    op.alter_column("vehicles", "color", type_=sa.String(50), existing_nullable=False)

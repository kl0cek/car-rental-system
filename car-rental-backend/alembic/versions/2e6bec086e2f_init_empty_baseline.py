"""init: empty baseline

Revision ID: 2e6bec086e2f
Revises:
Create Date: 2026-03-17 17:36:10.393323

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "2e6bec086e2f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

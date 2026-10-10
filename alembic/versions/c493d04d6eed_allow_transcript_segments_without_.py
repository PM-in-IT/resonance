"""Allow transcript segments without embeddings.

Revision ID: c493d04d6eed
Revises: 0001
"""

from collections.abc import Sequence

from pgvector.sqlalchemy import VECTOR

from alembic import op

revision: str = "c493d04d6eed"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "transcript_segments",
        "embedding",
        existing_type=VECTOR(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "transcript_segments",
        "embedding",
        existing_type=VECTOR(),
        nullable=False,
    )
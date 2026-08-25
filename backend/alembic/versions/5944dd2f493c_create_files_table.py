"""create files table

Revision ID: 5944dd2f493c
Revises: e2cb7813ace3
Create Date: 2026-08-18 23:02:33.627838
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5944dd2f493c"
down_revision: Union[str, None] = "e2cb7813ace3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("sha", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_files_id",
        "files",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_files_repository_id",
        "files",
        ["repository_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_files_repository_id",
        table_name="files",
    )

    op.drop_index(
        "ix_files_id",
        table_name="files",
    )

    op.drop_table("files")
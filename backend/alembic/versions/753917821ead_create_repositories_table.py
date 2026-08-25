"""create repositories table

Revision ID: 753917821ead
Revises: c1a8a2ca6df6
Create Date: 2026-08-18 22:17:47.379290
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "753917821ead"
down_revision: Union[str, None] = "c1a8a2ca6df6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
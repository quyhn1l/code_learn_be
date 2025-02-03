"""Update lessonprogess

Revision ID: 7c11f88e089b
Revises: 5c461a97aab6
Create Date: 2024-12-21 12:23:44.781337

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c11f88e089b"
down_revision: Union[str, None] = "5c461a97aab6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("lesson_progress", "video_progress")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "lesson_progress",
        sa.Column(
            "video_progress",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    # ### end Alembic commands ###

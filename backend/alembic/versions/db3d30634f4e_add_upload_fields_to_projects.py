"""add upload fields to projects

Revision ID: db3d30634f4e
Revises:
Create Date: 2026-07-02 23:32:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "db3d30634f4e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("uploaded_file_name", sa.String(255), nullable=True))
    op.add_column("projects", sa.Column("uploaded_file_size", sa.BigInteger(), nullable=True))
    op.add_column("projects", sa.Column("uploaded_file_path", sa.String(500), nullable=True))
    op.add_column("projects", sa.Column("upload_status", sa.String(20), nullable=True))
    op.add_column("projects", sa.Column("workspace_path", sa.String(500), nullable=True))
    op.add_column("projects", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "uploaded_at")
    op.drop_column("projects", "workspace_path")
    op.drop_column("projects", "upload_status")
    op.drop_column("projects", "uploaded_file_path")
    op.drop_column("projects", "uploaded_file_size")
    op.drop_column("projects", "uploaded_file_name")

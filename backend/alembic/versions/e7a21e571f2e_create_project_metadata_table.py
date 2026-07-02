"""create_project_metadata_table

Revision ID: e7a21e571f2e
Revises: 3682d05f65f3
Create Date: 2026-07-03 00:35:36.544252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7a21e571f2e'
down_revision: Union[str, None] = '3682d05f65f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('project_metadata',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.INTEGER(), nullable=False),
        sa.Column('primary_language', sa.VARCHAR(length=100), nullable=True),
        sa.Column('secondary_languages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('framework', sa.VARCHAR(length=100), nullable=True),
        sa.Column('package_manager', sa.VARCHAR(length=50), nullable=True),
        sa.Column('databases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('docker', sa.BOOLEAN(), nullable=False, server_default=sa.text('false')),
        sa.Column('docker_compose', sa.BOOLEAN(), nullable=False, server_default=sa.text('false')),
        sa.Column('kubernetes', sa.BOOLEAN(), nullable=False, server_default=sa.text('false')),
        sa.Column('ci_cd', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('config_files', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('has_readme', sa.BOOLEAN(), nullable=False, server_default=sa.text('false')),
        sa.Column('detected_languages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_folders', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_size_bytes', sa.BIGINT(), nullable=False, server_default=sa.text('0')),
        sa.Column('source_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('config_files_count', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('documentation_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('image_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('video_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('asset_files', sa.INTEGER(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_scanned_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id'),
    )
    op.create_index(op.f('ix_project_metadata_id'), 'project_metadata', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_project_metadata_id'), table_name='project_metadata')
    op.drop_table('project_metadata')

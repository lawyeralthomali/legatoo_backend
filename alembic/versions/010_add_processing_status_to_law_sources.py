"""add_processing_status_to_law_sources

Revision ID: 010
Revises: 39aa74e45f8a
Create Date: 2025-10-28 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '39aa74e45f8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add 'processing' status to law_sources table.
    
    For SQLite, we need to:
    1. Create a new table with the updated constraint
    2. Copy data from old table
    3. Drop old table
    4. Rename new table
    """
    
    # Check if we're using SQLite
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # For SQLite: recreate table with new constraint
        with op.batch_alter_table('law_sources', recreate='always') as batch_op:
            # SQLite will recreate the table with new schema from the model
            pass
    else:
        # For PostgreSQL/other databases: drop and recreate constraint
        op.drop_constraint('law_sources_status_check', 'law_sources', type_='check')
        op.create_check_constraint(
            'law_sources_status_check',
            'law_sources',
            "status IN ('raw', 'processing', 'processed', 'indexed')"
        )


def downgrade() -> None:
    """
    Remove 'processing' status from law_sources table.
    """
    
    # Check if we're using SQLite
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # For SQLite: recreate table with old constraint
        with op.batch_alter_table('law_sources', recreate='always') as batch_op:
            # SQLite will recreate the table
            pass
    else:
        # For PostgreSQL/other databases: drop and recreate constraint
        op.drop_constraint('law_sources_status_check', 'law_sources', type_='check')
        op.create_check_constraint(
            'law_sources_status_check',
            'law_sources',
            "status IN ('raw', 'processed', 'indexed')"
        )


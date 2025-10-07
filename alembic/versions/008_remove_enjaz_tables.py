"""remove_enjaz_tables

Revision ID: 008_remove_enjaz_tables
Revises: 007_add_document_id_to_legal_cases
Create Date: 2025-01-07 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_remove_enjaz_tables'
down_revision = '007_add_document_id_to_legal_cases'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove Enjaz-related tables."""
    # Drop enjaz_accounts table
    op.drop_table('enjaz_accounts')
    
    # Drop cases_imported table
    op.drop_table('cases_imported')


def downgrade() -> None:
    """Recreate Enjaz-related tables."""
    # Recreate enjaz_accounts table
    op.create_table('enjaz_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('password', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enjaz_accounts_user_id'), 'enjaz_accounts', ['user_id'], unique=False)
    
    # Recreate cases_imported table
    op.create_table('cases_imported',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=100), nullable=False),
        sa.Column('case_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=True),
        sa.Column('case_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'case_number', name='uq_user_case_number')
    )
    op.create_index(op.f('ix_cases_imported_user_id'), 'cases_imported', ['user_id'], unique=False)

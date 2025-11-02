"""Add case analysis history table

Revision ID: 011_add_case_analysis_history
Revises: 39aa74e45f8a
Create Date: 2025-11-02 14:00:00

Changes:
1. Add case_analyses table for storing legal case analysis history
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '011_add_case_analysis_history'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema with case analysis history table.
    """
    
    # Create case_analyses table
    op.create_table('case_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_size_mb', sa.Float(), nullable=True),
        sa.Column('analysis_type', sa.String(length=50), nullable=False),
        sa.Column('lawsuit_type', sa.String(length=100), nullable=False),
        sa.Column('result_seeking', sa.Text(), nullable=True),
        sa.Column('user_context', sa.Text(), nullable=True),
        sa.Column('analysis_data', sa.JSON(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_label', sa.String(length=20), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('additional_files', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_case_analyses_id'), 'case_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_case_analyses_user_id'), 'case_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_case_analyses_analysis_type'), 'case_analyses', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_case_analyses_created_at'), 'case_analyses', ['created_at'], unique=False)


def downgrade():
    """
    Downgrade database schema by removing case analysis history table.
    """
    
    # Drop indexes
    op.drop_index(op.f('ix_case_analyses_created_at'), table_name='case_analyses')
    op.drop_index(op.f('ix_case_analyses_analysis_type'), table_name='case_analyses')
    op.drop_index(op.f('ix_case_analyses_user_id'), table_name='case_analyses')
    op.drop_index(op.f('ix_case_analyses_id'), table_name='case_analyses')
    
    # Drop table
    op.drop_table('case_analyses')


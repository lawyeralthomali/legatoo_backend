"""add document_id to legal_cases

Revision ID: 007
Revises: 006
Create Date: 2025-10-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add document_id foreign key to legal_cases table."""
    
    # Add document_id column to legal_cases
    with op.batch_alter_table('legal_cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('document_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_legal_cases_document_id', ['document_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_legal_cases_document_id', 
            'knowledge_documents', 
            ['document_id'], 
            ['id'],
            ondelete='SET NULL'
        )
    
    # Update the knowledge_chunks_hierarchy index to include case_id
    # Note: SQLite doesn't support DROP INDEX IF EXISTS in some versions
    try:
        op.drop_index('idx_knowledge_chunks_hierarchy', table_name='knowledge_chunks')
    except:
        pass  # Index might not exist or already updated
    
    # Create updated index with case_id
    op.create_index(
        'idx_knowledge_chunks_hierarchy',
        'knowledge_chunks',
        ['law_source_id', 'branch_id', 'chapter_id', 'article_id', 'case_id'],
        unique=False
    )


def downgrade():
    """Remove document_id foreign key from legal_cases table."""
    
    # Recreate old index without case_id
    try:
        op.drop_index('idx_knowledge_chunks_hierarchy', table_name='knowledge_chunks')
    except:
        pass
    
    op.create_index(
        'idx_knowledge_chunks_hierarchy',
        'knowledge_chunks',
        ['law_source_id', 'branch_id', 'chapter_id', 'article_id'],
        unique=False
    )
    
    # Remove document_id from legal_cases
    with op.batch_alter_table('legal_cases', schema=None) as batch_op:
        batch_op.drop_constraint('fk_legal_cases_document_id', type_='foreignkey')
        batch_op.drop_index('ix_legal_cases_document_id')
        batch_op.drop_column('document_id')


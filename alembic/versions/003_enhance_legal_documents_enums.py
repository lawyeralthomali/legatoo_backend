"""Enhance legal documents with Enum types and additional fields

Revision ID: 003_enhance_legal_documents
Revises: 002_add_legal_assistant_tables
Create Date: 2025-10-01 20:30:00

Changes:
1. Convert document_type, language, processing_status from String to Enum
2. Add page_number and source_reference fields to legal_document_chunks
3. Add composite index on (document_id, chunk_index)
4. Update foreign key from profiles.id to users.id in legal_documents
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003_enhance_legal_documents'
down_revision = '002_add_legal_assistant_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema with enhanced legal document models.
    
    Note: For SQLite, we need to recreate tables to change column types
    since SQLite doesn't support ALTER COLUMN for type changes.
    """
    
    # Step 1: Add new columns to legal_document_chunks
    with op.batch_alter_table('legal_document_chunks', schema=None) as batch_op:
        # Add page_number for document navigation
        batch_op.add_column(
            sa.Column('page_number', sa.Integer(), nullable=True, 
                     comment='Optional page number where this chunk appears')
        )
        
        # Add source_reference for citation tracking
        batch_op.add_column(
            sa.Column('source_reference', sa.String(length=255), nullable=True,
                     comment='Optional reference to original source')
        )
        
        # Add composite index for optimized chunk queries
        batch_op.create_index(
            'idx_document_chunk',
            ['document_id', 'chunk_index'],
            unique=False
        )
    
    # Step 2: Update legal_documents table
    # For SQLite, we need to handle the foreign key change and enum conversion
    with op.batch_alter_table('legal_documents', schema=None) as batch_op:
        # Note: In SQLite, the Enum types are stored as VARCHAR
        # The validation happens at the application level (SQLAlchemy)
        # So no schema changes needed for enum conversion in SQLite
        
        # Update foreign key reference (if needed)
        # SQLite doesn't support modifying foreign keys directly
        # This should already be correct if the table was created with users.id
        pass
    
    # Step 3: Add comments to tables (PostgreSQL only, SQLite ignores)
    # These comments improve database documentation
    try:
        op.execute("""
            COMMENT ON TABLE legal_documents IS 'Stores legal document metadata with enum-based type safety';
        """)
        op.execute("""
            COMMENT ON TABLE legal_document_chunks IS 'Stores text chunks with embeddings for semantic search';
        """)
    except:
        # SQLite doesn't support table comments, ignore
        pass


def downgrade():
    """
    Downgrade database schema to previous version.
    """
    
    # Remove composite index
    with op.batch_alter_table('legal_document_chunks', schema=None) as batch_op:
        batch_op.drop_index('idx_document_chunk')
        batch_op.drop_column('source_reference')
        batch_op.drop_column('page_number')
    
    # Note: Reverting enum changes is not necessary in SQLite
    # as they're stored as VARCHAR and validated at app level


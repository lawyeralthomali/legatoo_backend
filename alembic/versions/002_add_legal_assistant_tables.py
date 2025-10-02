"""add_legal_assistant_tables

Revision ID: 002_legal_assistant
Revises: 001_add_contract_management_tables
Create Date: 2025-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_add_legal_assistant_tables'
down_revision = '001_add_contract_management_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create legal_documents table
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='ar'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_documents_id'), 'legal_documents', ['id'], unique=False)
    
    # Create legal_document_chunks table
    op.create_table(
        'legal_document_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('article_number', sa.String(length=50), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_document_chunks_id'), 'legal_document_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_legal_document_chunks_document_id'), 'legal_document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_legal_document_chunks_article_number'), 'legal_document_chunks', ['article_number'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_legal_document_chunks_article_number'), table_name='legal_document_chunks')
    op.drop_index(op.f('ix_legal_document_chunks_document_id'), table_name='legal_document_chunks')
    op.drop_index(op.f('ix_legal_document_chunks_id'), table_name='legal_document_chunks')
    op.drop_table('legal_document_chunks')
    
    op.drop_index(op.f('ix_legal_documents_id'), table_name='legal_documents')
    op.drop_table('legal_documents')


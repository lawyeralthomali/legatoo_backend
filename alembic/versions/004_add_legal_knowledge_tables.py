"""Add legal knowledge management tables

Revision ID: 004_add_legal_knowledge_tables
Revises: 003_enhance_legal_documents
Create Date: 2025-01-27 10:00:00

Changes:
1. Add law_sources table for legal sources (laws, regulations, codes)
2. Add law_articles table for articles and clauses of laws
3. Add legal_cases table for legal precedents and judgments
4. Add case_sections table for structured parts of cases
5. Add legal_terms table for legal terms and definitions
6. Add knowledge_documents table for uploaded files
7. Add knowledge_chunks table for document segments
8. Add analysis_results table for AI analysis outputs
9. Add knowledge_links table for relationships between knowledge items
10. Add knowledge_metadata table for tracking ingestion and curation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004_add_legal_knowledge_tables'
down_revision = '003_enhance_legal_documents'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema with legal knowledge management tables.
    """
    
    # Create law_sources table
    op.create_table('law_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('issuing_authority', sa.String(length=200), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('last_update', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('upload_file_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("type IN ('law', 'regulation', 'code', 'directive', 'decree')", name='ck_law_sources_type'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_law_sources_id'), 'law_sources', ['id'], unique=False)
    op.create_index(op.f('ix_law_sources_name'), 'law_sources', ['name'], unique=False)
    op.create_index(op.f('ix_law_sources_jurisdiction'), 'law_sources', ['jurisdiction'], unique=False)
    op.create_index('idx_law_sources_type_jurisdiction', 'law_sources', ['type', 'jurisdiction'], unique=False)
    
    # Create law_articles table
    op.create_table('law_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('law_source_id', sa.Integer(), nullable=False),
        sa.Column('article_number', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['law_source_id'], ['law_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_law_articles_id'), 'law_articles', ['id'], unique=False)
    op.create_index(op.f('ix_law_articles_law_source_id'), 'law_articles', ['law_source_id'], unique=False)
    op.create_index(op.f('ix_law_articles_article_number'), 'law_articles', ['article_number'], unique=False)
    op.create_index('idx_law_articles_keywords', 'law_articles', ['keywords'], unique=False)
    
    # Create legal_cases table
    op.create_table('legal_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('court_name', sa.String(length=200), nullable=True),
        sa.Column('decision_date', sa.Date(), nullable=True),
        sa.Column('involved_parties', sa.Text(), nullable=True),
        sa.Column('pdf_path', sa.Text(), nullable=True),
        sa.Column('source_reference', sa.Text(), nullable=True),
        sa.Column('case_type', sa.String(length=50), nullable=True),
        sa.Column('court_level', sa.String(length=50), nullable=True),
        sa.Column('case_outcome', sa.String(length=100), nullable=True),
        sa.Column('judge_names', sa.JSON(), nullable=True),
        sa.Column('claim_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_cases_id'), 'legal_cases', ['id'], unique=False)
    op.create_index(op.f('ix_legal_cases_case_number'), 'legal_cases', ['case_number'], unique=False)
    op.create_index(op.f('ix_legal_cases_jurisdiction'), 'legal_cases', ['jurisdiction'], unique=False)
    op.create_index(op.f('ix_legal_cases_decision_date'), 'legal_cases', ['decision_date'], unique=False)
    op.create_index('idx_legal_cases_jurisdiction_date', 'legal_cases', ['jurisdiction', 'decision_date'], unique=False)
    
    # Create case_sections table
    op.create_table('case_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('section_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint("section_type IN ('summary', 'facts', 'arguments', 'ruling', 'legal_basis')", name='ck_case_sections_section_type'),
        sa.ForeignKeyConstraint(['case_id'], ['legal_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_sections_id'), 'case_sections', ['id'], unique=False)
    op.create_index(op.f('ix_case_sections_case_id'), 'case_sections', ['case_id'], unique=False)
    op.create_index('idx_case_sections_type', 'case_sections', ['section_type'], unique=False)
    
    # Create legal_terms table
    op.create_table('legal_terms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('term', sa.Text(), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('related_terms', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_terms_id'), 'legal_terms', ['id'], unique=False)
    op.create_index(op.f('ix_legal_terms_term'), 'legal_terms', ['term'], unique=False)
    
    # Create knowledge_documents table
    op.create_table('knowledge_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_metadata', sa.JSON(), nullable=True),
        sa.CheckConstraint("category IN ('law', 'case', 'contract', 'article', 'policy', 'manual')", name='ck_knowledge_documents_category'),
        sa.CheckConstraint("source_type IN ('uploaded', 'web_scraped', 'api_import')", name='ck_knowledge_documents_source_type'),
        sa.CheckConstraint("status IN ('raw', 'processed', 'indexed')", name='ck_knowledge_documents_status'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_documents_id'), 'knowledge_documents', ['id'], unique=False)
    op.create_index('idx_knowledge_documents_category_status', 'knowledge_documents', ['category', 'status'], unique=False)
    
    # Create knowledge_chunks table
    op.create_table('knowledge_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens_count', sa.Integer(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('law_source_ref', sa.Integer(), nullable=True),
        sa.Column('case_ref', sa.Integer(), nullable=True),
        sa.Column('term_ref', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['case_ref'], ['legal_cases.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['law_source_ref'], ['law_sources.id'], ),
        sa.ForeignKeyConstraint(['term_ref'], ['legal_terms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_chunks_id'), 'knowledge_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_chunks_document_id'), 'knowledge_chunks', ['document_id'], unique=False)
    op.create_index('idx_knowledge_chunks_tokens', 'knowledge_chunks', ['tokens_count'], unique=False)
    
    # Create analysis_results table
    op.create_table('analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('output', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint("analysis_type IN ('summary', 'classification', 'entity_extraction', 'law_linking', 'case_linking')", name='ck_analysis_results_analysis_type'),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_results_id'), 'analysis_results', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_results_document_id'), 'analysis_results', ['document_id'], unique=False)
    op.create_index('idx_analysis_results_type_confidence', 'analysis_results', ['analysis_type', 'confidence'], unique=False)
    
    # Create knowledge_links table
    op.create_table('knowledge_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('relation', sa.String(length=50), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint("relation IN ('cites', 'interprets', 'contradicts', 'based_on', 'explains')", name='ck_knowledge_links_relation'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_links_id'), 'knowledge_links', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_links_source_type'), 'knowledge_links', ['source_type'], unique=False)
    op.create_index(op.f('ix_knowledge_links_source_id'), 'knowledge_links', ['source_id'], unique=False)
    op.create_index(op.f('ix_knowledge_links_target_type'), 'knowledge_links', ['target_type'], unique=False)
    op.create_index(op.f('ix_knowledge_links_target_id'), 'knowledge_links', ['target_id'], unique=False)
    op.create_index('idx_knowledge_links_source_target', 'knowledge_links', ['source_type', 'source_id', 'target_type', 'target_id'], unique=False)
    
    # Create knowledge_metadata table
    op.create_table('knowledge_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('object_type', sa.String(length=50), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_metadata_id'), 'knowledge_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_metadata_object_type'), 'knowledge_metadata', ['object_type'], unique=False)
    op.create_index(op.f('ix_knowledge_metadata_object_id'), 'knowledge_metadata', ['object_id'], unique=False)
    op.create_index(op.f('ix_knowledge_metadata_key'), 'knowledge_metadata', ['key'], unique=False)
    op.create_index('idx_knowledge_metadata_object_key', 'knowledge_metadata', ['object_type', 'object_id', 'key'], unique=False)


def downgrade():
    """
    Downgrade database schema by removing legal knowledge management tables.
    """
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('knowledge_metadata')
    op.drop_table('knowledge_links')
    op.drop_table('analysis_results')
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('legal_terms')
    op.drop_table('case_sections')
    op.drop_table('legal_cases')
    op.drop_table('law_articles')
    op.drop_table('law_sources')

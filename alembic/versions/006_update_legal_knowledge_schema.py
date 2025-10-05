"""Update legal knowledge schema with unified document references and tracking fields

Revision ID: 006_update_legal_knowledge_schema
Revises: 005_add_hierarchical_structure
Create Date: 2025-10-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '006_update_legal_knowledge_schema'
down_revision = '005_add_hierarchical_structure'
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema changes"""
    
    # 1. LawSource modifications
    # Remove upload_file_path column
    with op.batch_alter_table('law_sources', schema=None) as batch_op:
        batch_op.drop_column('upload_file_path')
        # Add knowledge_document_id FK
        batch_op.add_column(sa.Column('knowledge_document_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_law_sources_knowledge_document', 'knowledge_documents', ['knowledge_document_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_law_sources_knowledge_document_id', ['knowledge_document_id'])
        # Add status column
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=True, server_default='raw'))
        batch_op.create_check_constraint('ck_law_sources_status', "status IN ('raw', 'processed', 'indexed')")
        batch_op.create_index('ix_law_sources_status', ['status'])
    
    # 2. LawBranch - Add source_document_id
    with op.batch_alter_table('law_branches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_document_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_law_branches_source_document', 'knowledge_documents', ['source_document_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_law_branches_source_document_id', ['source_document_id'])
    
    # 3. LawChapter - Add source_document_id
    with op.batch_alter_table('law_chapters', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_document_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_law_chapters_source_document', 'knowledge_documents', ['source_document_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_law_chapters_source_document_id', ['source_document_id'])
    
    # 4. LawArticle - Add ai_processed_at and source_document_id
    with op.batch_alter_table('law_articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_processed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('source_document_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_law_articles_source_document', 'knowledge_documents', ['source_document_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_law_articles_source_document_id', ['source_document_id'])
    
    # 5. LegalCase - Add status column
    with op.batch_alter_table('legal_cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=True, server_default='raw'))
        batch_op.create_check_constraint('ck_legal_cases_status', "status IN ('raw', 'processed', 'indexed')")
        batch_op.create_index('ix_legal_cases_status', ['status'])
    
    # 6. CaseSection - Add ai_processed_at
    with op.batch_alter_table('case_sections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_processed_at', sa.DateTime(timezone=True), nullable=True))
    
    # 7. KnowledgeChunk - Add verified_by_admin
    with op.batch_alter_table('knowledge_chunks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verified_by_admin', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.create_index('ix_knowledge_chunks_verified_by_admin', ['verified_by_admin'])
    
    # 8. KnowledgeDocument - Add file_hash
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_hash', sa.String(length=64), nullable=True))
        batch_op.create_index('ix_knowledge_documents_file_hash', ['file_hash'], unique=True)
    
    # 9. AnalysisResult - Add processed_by
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('processed_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_analysis_results_processed_by', 'users', ['processed_by'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_analysis_results_processed_by', ['processed_by'])


def downgrade():
    """Revert schema changes"""
    
    # 9. AnalysisResult - Remove processed_by
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.drop_index('ix_analysis_results_processed_by')
        batch_op.drop_constraint('fk_analysis_results_processed_by', type_='foreignkey')
        batch_op.drop_column('processed_by')
    
    # 8. KnowledgeDocument - Remove file_hash
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.drop_index('ix_knowledge_documents_file_hash')
        batch_op.drop_column('file_hash')
    
    # 7. KnowledgeChunk - Remove verified_by_admin
    with op.batch_alter_table('knowledge_chunks', schema=None) as batch_op:
        batch_op.drop_index('ix_knowledge_chunks_verified_by_admin')
        batch_op.drop_column('verified_by_admin')
    
    # 6. CaseSection - Remove ai_processed_at
    with op.batch_alter_table('case_sections', schema=None) as batch_op:
        batch_op.drop_column('ai_processed_at')
    
    # 5. LegalCase - Remove status
    with op.batch_alter_table('legal_cases', schema=None) as batch_op:
        batch_op.drop_index('ix_legal_cases_status')
        batch_op.drop_constraint('ck_legal_cases_status', type_='check')
        batch_op.drop_column('status')
    
    # 4. LawArticle - Remove ai_processed_at and source_document_id
    with op.batch_alter_table('law_articles', schema=None) as batch_op:
        batch_op.drop_index('ix_law_articles_source_document_id')
        batch_op.drop_constraint('fk_law_articles_source_document', type_='foreignkey')
        batch_op.drop_column('source_document_id')
        batch_op.drop_column('ai_processed_at')
    
    # 3. LawChapter - Remove source_document_id
    with op.batch_alter_table('law_chapters', schema=None) as batch_op:
        batch_op.drop_index('ix_law_chapters_source_document_id')
        batch_op.drop_constraint('fk_law_chapters_source_document', type_='foreignkey')
        batch_op.drop_column('source_document_id')
    
    # 2. LawBranch - Remove source_document_id
    with op.batch_alter_table('law_branches', schema=None) as batch_op:
        batch_op.drop_index('ix_law_branches_source_document_id')
        batch_op.drop_constraint('fk_law_branches_source_document', type_='foreignkey')
        batch_op.drop_column('source_document_id')
    
    # 1. LawSource - Revert modifications
    with op.batch_alter_table('law_sources', schema=None) as batch_op:
        batch_op.drop_index('ix_law_sources_status')
        batch_op.drop_constraint('ck_law_sources_status', type_='check')
        batch_op.drop_column('status')
        batch_op.drop_index('ix_law_sources_knowledge_document_id')
        batch_op.drop_constraint('fk_law_sources_knowledge_document', type_='foreignkey')
        batch_op.drop_column('knowledge_document_id')
        # Restore upload_file_path
        batch_op.add_column(sa.Column('upload_file_path', sa.Text(), nullable=True))

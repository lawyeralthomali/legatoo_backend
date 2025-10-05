"""Add hierarchical structure to legal knowledge tables

Revision ID: 005_add_hierarchical_structure
Revises: 004_add_legal_knowledge_tables
Create Date: 2025-01-27 12:00:00

Changes:
1. Add law_branches table for main branches/sections in legal sources
2. Add law_chapters table for chapters within branches
3. Update law_articles table to include branch_id and chapter_id foreign keys
4. Add order_index columns for proper ordering
5. Update knowledge_chunks table with hierarchical foreign keys
6. Add comprehensive indexes for performance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '005_add_hierarchical_structure'
down_revision = '004_add_legal_knowledge_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema with hierarchical structure support.
    """
    
    # Create law_branches table
    op.create_table('law_branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('law_source_id', sa.Integer(), nullable=False),
        sa.Column('branch_number', sa.String(length=20), nullable=True),
        sa.Column('branch_name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['law_source_id'], ['law_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_law_branches_id'), 'law_branches', ['id'], unique=False)
    op.create_index(op.f('ix_law_branches_law_source_id'), 'law_branches', ['law_source_id'], unique=False)
    op.create_index(op.f('ix_law_branches_branch_number'), 'law_branches', ['branch_number'], unique=False)
    op.create_index('idx_law_branches_source_number', 'law_branches', ['law_source_id', 'branch_number'], unique=False)
    
    # Create law_chapters table
    op.create_table('law_chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('chapter_number', sa.String(length=20), nullable=True),
        sa.Column('chapter_name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['law_branches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_law_chapters_id'), 'law_chapters', ['id'], unique=False)
    op.create_index(op.f('ix_law_chapters_branch_id'), 'law_chapters', ['branch_id'], unique=False)
    op.create_index(op.f('ix_law_chapters_chapter_number'), 'law_chapters', ['chapter_number'], unique=False)
    op.create_index('idx_law_chapters_branch_number', 'law_chapters', ['branch_id', 'chapter_number'], unique=False)
    
    # Add new columns to law_articles table
    op.add_column('law_articles', sa.Column('branch_id', sa.Integer(), nullable=True))
    op.add_column('law_articles', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.add_column('law_articles', sa.Column('order_index', sa.Integer(), nullable=True))
    
    # Add foreign key constraints to law_articles
    op.create_foreign_key('fk_law_articles_branch_id', 'law_articles', 'law_branches', ['branch_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_law_articles_chapter_id', 'law_articles', 'law_chapters', ['chapter_id'], ['id'], ondelete='CASCADE')
    
    # Create new indexes for law_articles
    op.create_index(op.f('ix_law_articles_branch_id'), 'law_articles', ['branch_id'], unique=False)
    op.create_index(op.f('ix_law_articles_chapter_id'), 'law_articles', ['chapter_id'], unique=False)
    op.create_index('idx_law_articles_hierarchy', 'law_articles', ['law_source_id', 'branch_id', 'chapter_id'], unique=False)
    op.create_index('idx_law_articles_chapter_order', 'law_articles', ['chapter_id', 'order_index'], unique=False)
    
    # Update knowledge_chunks table with hierarchical foreign keys
    op.add_column('knowledge_chunks', sa.Column('branch_id', sa.Integer(), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('article_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraints to knowledge_chunks
    op.create_foreign_key('fk_knowledge_chunks_branch_id', 'knowledge_chunks', 'law_branches', ['branch_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_knowledge_chunks_chapter_id', 'knowledge_chunks', 'law_chapters', ['chapter_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_knowledge_chunks_article_id', 'knowledge_chunks', 'law_articles', ['article_id'], ['id'], ondelete='CASCADE')
    
    # Create new indexes for knowledge_chunks
    op.create_index(op.f('ix_knowledge_chunks_branch_id'), 'knowledge_chunks', ['branch_id'], unique=False)
    op.create_index(op.f('ix_knowledge_chunks_chapter_id'), 'knowledge_chunks', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_knowledge_chunks_article_id'), 'knowledge_chunks', ['article_id'], unique=False)
    op.create_index('idx_knowledge_chunks_hierarchy', 'knowledge_chunks', ['law_source_ref', 'branch_id', 'chapter_id', 'article_id'], unique=False)


def downgrade():
    """
    Downgrade database schema by removing hierarchical structure.
    """
    
    # Drop indexes first
    op.drop_index('idx_knowledge_chunks_hierarchy', table_name='knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_chunks_article_id'), table_name='knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_chunks_chapter_id'), table_name='knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_chunks_branch_id'), table_name='knowledge_chunks')
    
    # Drop foreign key constraints from knowledge_chunks
    op.drop_constraint('fk_knowledge_chunks_article_id', 'knowledge_chunks', type_='foreignkey')
    op.drop_constraint('fk_knowledge_chunks_chapter_id', 'knowledge_chunks', type_='foreignkey')
    op.drop_constraint('fk_knowledge_chunks_branch_id', 'knowledge_chunks', type_='foreignkey')
    
    # Drop columns from knowledge_chunks
    op.drop_column('knowledge_chunks', 'article_id')
    op.drop_column('knowledge_chunks', 'chapter_id')
    op.drop_column('knowledge_chunks', 'branch_id')
    
    # Drop indexes from law_articles
    op.drop_index('idx_law_articles_chapter_order', table_name='law_articles')
    op.drop_index('idx_law_articles_hierarchy', table_name='law_articles')
    op.drop_index(op.f('ix_law_articles_chapter_id'), table_name='law_articles')
    op.drop_index(op.f('ix_law_articles_branch_id'), table_name='law_articles')
    
    # Drop foreign key constraints from law_articles
    op.drop_constraint('fk_law_articles_chapter_id', 'law_articles', type_='foreignkey')
    op.drop_constraint('fk_law_articles_branch_id', 'law_articles', type_='foreignkey')
    
    # Drop columns from law_articles
    op.drop_column('law_articles', 'order_index')
    op.drop_column('law_articles', 'chapter_id')
    op.drop_column('law_articles', 'branch_id')
    
    # Drop law_chapters table
    op.drop_table('law_chapters')
    
    # Drop law_branches table
    op.drop_table('law_branches')

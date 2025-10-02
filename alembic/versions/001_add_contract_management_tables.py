"""Add contract management tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_contract_management_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create contract_categories table
    op.create_table('contract_categories',
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name_ar', sa.String(length=150), nullable=False),
        sa.Column('name_en', sa.String(length=150), nullable=False),
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('legal_field', sa.String(length=50), nullable=True),
        sa.Column('business_scope', sa.String(length=50), nullable=True),
        sa.Column('complexity_level', sa.String(length=20), nullable=True),
        sa.Column('contract_type', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('color_code', sa.String(length=7), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('template_count', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['contract_categories.category_id'], ),
        sa.PrimaryKeyConstraint('category_id')
    )
    op.create_index(op.f('ix_contract_categories_category_id'), 'contract_categories', ['category_id'], unique=False)

    # Create contract_templates table
    op.create_table('contract_templates',
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('title_ar', sa.String(length=200), nullable=False),
        sa.Column('title_en', sa.String(length=200), nullable=False),
        sa.Column('description_ar', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('contract_structure', sa.JSON(), nullable=False),
        sa.Column('variables_schema', sa.JSON(), nullable=True),
        sa.Column('base_language', sa.String(length=10), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('requires_legal_review', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('avg_rating', sa.Integer(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['contract_categories.category_id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('template_id')
    )
    op.create_index(op.f('ix_contract_templates_template_id'), 'contract_templates', ['template_id'], unique=False)

    # Create user_contracts table
    op.create_table('user_contracts',
        sa.Column('user_contract_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('contract_data', sa.JSON(), nullable=True),
        sa.Column('final_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['contract_templates.template_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_contract_id')
    )
    op.create_index(op.f('ix_user_contracts_user_contract_id'), 'user_contracts', ['user_contract_id'], unique=False)

    # Create user_favorites table
    op.create_table('user_favorites',
        sa.Column('favorite_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['contract_templates.template_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('favorite_id')
    )
    op.create_index(op.f('ix_user_favorites_favorite_id'), 'user_favorites', ['favorite_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_user_favorites_favorite_id'), table_name='user_favorites')
    op.drop_table('user_favorites')
    
    op.drop_index(op.f('ix_user_contracts_user_contract_id'), table_name='user_contracts')
    op.drop_table('user_contracts')
    
    op.drop_index(op.f('ix_contract_templates_template_id'), table_name='contract_templates')
    op.drop_table('contract_templates')
    
    op.drop_index(op.f('ix_contract_categories_category_id'), table_name='contract_categories')
    op.drop_table('contract_categories')

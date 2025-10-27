"""add_file_extension_to_knowledge_document

Revision ID: 38ee63f33d7f
Revises: 009_add_embedding_vector
Create Date: 2025-10-25 18:29:58.443933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38ee63f33d7f'
down_revision = '003_enhance_legal_documents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add file_extension column to knowledge_documents if it doesn't exist
    try:
        op.add_column('knowledge_documents', 
                      sa.Column('file_extension', sa.String(20), nullable=True))
    except Exception as e:
        print(f"Note: Column file_extension may already exist: {e}")
    
    # Update status constraint to include 'pending_parsing' if the constraint exists
    try:
        op.drop_constraint('knowledge_documents_status_check', 'knowledge_documents', type_='check')
        op.create_check_constraint(
            'knowledge_documents_status_check',
            'knowledge_documents',
            'status IN (\'raw\', \'processed\', \'indexed\', \'pending_parsing\')'
        )
    except Exception as e:
        print(f"Note: Status constraint update skipped: {e}")


def downgrade() -> None:
    # Remove the new status value
    try:
        op.drop_constraint('knowledge_documents_status_check', 'knowledge_documents', type_='check')
        op.create_check_constraint(
            'knowledge_documents_status_check',
            'knowledge_documents',
            'status IN (\'raw\', \'processed\', \'indexed\')'
        )
    except Exception as e:
        print(f"Note: Constraint downgrade skipped: {e}")
    
    # Remove file_extension column
    try:
        op.drop_column('knowledge_documents', 'file_extension')
    except Exception as e:
        print(f"Note: Column drop skipped: {e}")

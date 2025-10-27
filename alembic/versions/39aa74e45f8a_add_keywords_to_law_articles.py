"""add_keywords_to_law_articles

Revision ID: 39aa74e45f8a
Revises: 38ee63f33d7f
Create Date: 2025-10-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '39aa74e45f8a'
down_revision = '624d950b940b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add keywords column to law_articles if it doesn't exist
    try:
        op.add_column('law_articles', 
                      sa.Column('keywords', sa.JSON(), nullable=True))
    except Exception as e:
        print(f"Note: Column keywords may already exist: {e}")


def downgrade() -> None:
    # Remove keywords column
    try:
        op.drop_column('law_articles', 'keywords')
    except Exception as e:
        print(f"Note: Column drop skipped: {e}")


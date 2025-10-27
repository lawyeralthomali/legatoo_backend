"""merge_heads

Revision ID: 624d950b940b
Revises: 009_add_embedding_vector, 38ee63f33d7f
Create Date: 2025-10-25 18:32:57.311157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '624d950b940b'
down_revision = ('009_add_embedding_vector', '38ee63f33d7f')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

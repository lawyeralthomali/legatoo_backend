"""Update profiles table structure

Revision ID: update_profiles_structure
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_profiles_structure'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade():
    """Update profiles table to new structure"""
    
    # Add new columns
    op.add_column('profiles', sa.Column('first_name', sa.Text(), nullable=True))
    op.add_column('profiles', sa.Column('last_name', sa.Text(), nullable=True))
    op.add_column('profiles', sa.Column('phone_number', sa.Text(), nullable=True))
    op.add_column('profiles', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('profiles', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Migrate existing data
    connection = op.get_bind()
    
    # Update first_name and last_name from full_name
    connection.execute(sa.text("""
        UPDATE profiles 
        SET 
            first_name = CASE 
                WHEN full_name IS NULL OR full_name = '' THEN 'User'
                WHEN position(' ' in full_name) = 0 THEN full_name
                ELSE split_part(full_name, ' ', 1)
            END,
            last_name = CASE 
                WHEN full_name IS NULL OR full_name = '' THEN 'User'
                WHEN position(' ' in full_name) = 0 THEN 'User'
                ELSE substring(full_name from position(' ' in full_name) + 1)
            END,
            created_at = NOW()
        WHERE first_name IS NULL
    """))
    
    # Make required fields NOT NULL
    op.alter_column('profiles', 'first_name', nullable=False)
    op.alter_column('profiles', 'last_name', nullable=False)
    op.alter_column('profiles', 'created_at', nullable=False)
    
    # Add constraints
    op.create_check_constraint(
        'check_first_name_length',
        'profiles',
        'length(first_name) >= 1 AND length(first_name) <= 100'
    )
    op.create_check_constraint(
        'check_last_name_length',
        'profiles',
        'length(last_name) >= 1 AND length(last_name) <= 100'
    )
    op.create_check_constraint(
        'check_phone_number_length',
        'profiles',
        'phone_number IS NULL OR length(phone_number) <= 20'
    )
    
    # Create indexes
    op.create_index('idx_profiles_first_name', 'profiles', ['first_name'])
    op.create_index('idx_profiles_last_name', 'profiles', ['last_name'])
    op.create_index('idx_profiles_account_type', 'profiles', ['account_type'])
    op.create_index('idx_profiles_created_at', 'profiles', ['created_at'])


def downgrade():
    """Rollback profiles table changes"""
    
    # Drop indexes
    op.drop_index('idx_profiles_created_at', table_name='profiles')
    op.drop_index('idx_profiles_account_type', table_name='profiles')
    op.drop_index('idx_profiles_last_name', table_name='profiles')
    op.drop_index('idx_profiles_first_name', table_name='profiles')
    
    # Drop constraints
    op.drop_constraint('check_phone_number_length', 'profiles', type_='check')
    op.drop_constraint('check_last_name_length', 'profiles', type_='check')
    op.drop_constraint('check_first_name_length', 'profiles', type_='check')
    
    # Reconstruct full_name before dropping columns
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE profiles 
        SET full_name = CONCAT(first_name, ' ', last_name)
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
    """))
    
    # Drop new columns
    op.drop_column('profiles', 'updated_at')
    op.drop_column('profiles', 'created_at')
    op.drop_column('profiles', 'phone_number')
    op.drop_column('profiles', 'last_name')
    op.drop_column('profiles', 'first_name')

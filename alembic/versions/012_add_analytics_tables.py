"""add_analytics_tables

Revision ID: 012_add_analytics
Revises: 6595bc39b441
Create Date: 2025-01-16 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '012_add_analytics'
down_revision = '6595bc39b441'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist before creating them (handles case where create_tables already created them)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # Create user_sessions table
    if 'user_sessions' not in existing_tables:
        op.create_table(
            'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
        op.create_index(op.f('ix_user_sessions_last_seen'), 'user_sessions', ['last_seen'], unique=False)
    else:
        # Create indexes if they don't exist
        try:
            op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
        except:
            pass
        try:
            op.create_index(op.f('ix_user_sessions_last_seen'), 'user_sessions', ['last_seen'], unique=False)
        except:
            pass
    
    # Create login_history table
    if 'login_history' not in existing_tables:
        op.create_table(
            'login_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('login_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('device', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_login_history_user_id'), 'login_history', ['user_id'], unique=False)
        op.create_index(op.f('ix_login_history_login_time'), 'login_history', ['login_time'], unique=False)
        op.create_index(op.f('ix_login_history_status'), 'login_history', ['status'], unique=False)
    else:
        # Create indexes if they don't exist
        for index_name in ['ix_login_history_user_id', 'ix_login_history_login_time', 'ix_login_history_status']:
            try:
                op.create_index(op.f(index_name), 'login_history', [index_name.replace('ix_login_history_', '')], unique=False)
            except:
                pass
    
    # Create system_logs table
    if 'system_logs' not in existing_tables:
        op.create_table(
            'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_system_logs_level'), 'system_logs', ['level'], unique=False)
        op.create_index(op.f('ix_system_logs_endpoint'), 'system_logs', ['endpoint'], unique=False)
        op.create_index(op.f('ix_system_logs_created_at'), 'system_logs', ['created_at'], unique=False)
        op.create_index(op.f('ix_system_logs_correlation_id'), 'system_logs', ['correlation_id'], unique=False)
        op.create_index(op.f('ix_system_logs_user_id'), 'system_logs', ['user_id'], unique=False)
    else:
        # Create indexes if they don't exist
        indexes = [
            ('ix_system_logs_level', 'level'),
            ('ix_system_logs_endpoint', 'endpoint'),
            ('ix_system_logs_created_at', 'created_at'),
            ('ix_system_logs_correlation_id', 'correlation_id'),
            ('ix_system_logs_user_id', 'user_id')
        ]
        for index_name, column in indexes:
            try:
                op.create_index(op.f(index_name), 'system_logs', [column], unique=False)
            except:
                pass


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_system_logs_user_id'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_correlation_id'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_created_at'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_endpoint'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_level'), table_name='system_logs')
    op.drop_index(op.f('ix_login_history_status'), table_name='login_history')
    op.drop_index(op.f('ix_login_history_login_time'), table_name='login_history')
    op.drop_index(op.f('ix_login_history_user_id'), table_name='login_history')
    op.drop_index(op.f('ix_user_sessions_last_seen'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    
    # Drop tables
    op.drop_table('system_logs')
    op.drop_table('login_history')
    op.drop_table('user_sessions')

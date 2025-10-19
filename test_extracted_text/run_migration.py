"""Temporary script to run database migration."""
import sys
import traceback

try:
    from alembic.config import Config
    from alembic import command
    
    print("🔧 Running database migration...")
    cfg = Config('alembic.ini')
    command.upgrade(cfg, 'head')
    print("✅ Migration completed successfully!")
except Exception as e:
    print(f"❌ Migration failed: {str(e)}")
    traceback.print_exc()
    sys.exit(1)


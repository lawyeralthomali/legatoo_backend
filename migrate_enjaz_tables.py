"""
Migration script to create Enjaz-related tables.

This script creates the necessary database tables for Enjaz integration.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import create_tables
from app.config.enhanced_logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def migrate_enjaz_tables():
    """Create Enjaz-related database tables."""
    try:
        logger.info("Starting Enjaz tables migration...")
        
        # Create all tables (including new Enjaz tables)
        await create_tables()
        
        logger.info("✅ Enjaz tables migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Enjaz tables migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_enjaz_tables())

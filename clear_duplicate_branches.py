#!/usr/bin/env python3
"""
Script to clear duplicate branches from the database.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.repositories.legal_knowledge_repository import LawSourceRepository, LawArticleRepository
from app.db.database import get_db

async def clear_duplicate_branches():
    """Clear all branches and related data to start fresh."""
    
    print("Clearing duplicate branches from database...")
    print("=" * 50)
    
    try:
        # Get database session
        async for db in get_db():
            source_repo = LawSourceRepository(db)
            article_repo = LawArticleRepository(db)
            break
        
        # Get all law sources
        sources, total = await source_repo.get_law_sources()
        print(f"Found {total} law sources")
        
        for source in sources:
            print(f"\nProcessing source: {source.name} (ID: {source.id})")
            
            # Get branches for this source
            branches = await source_repo.get_branches_by_source_id(source.id)
            print(f"  Found {len(branches)} branches")
            
            if branches:
                # Delete all articles first (they have foreign key constraints)
                for branch in branches:
                    # Delete articles in this branch
                    branch_articles = await article_repo.get_by_branch_id(branch.id)
                    print(f"    Deleting {len(branch_articles)} articles from branch {branch.id}")
                    
                    for article in branch_articles:
                        await db.delete(article)
                
                # Delete all branches
                print(f"  Deleting {len(branches)} branches")
                for branch in branches:
                    await db.delete(branch)
                
                await db.commit()
                print(f"  Successfully cleared branches for source {source.id}")
        
        print("\nDatabase cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error clearing branches: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_duplicate_branches())

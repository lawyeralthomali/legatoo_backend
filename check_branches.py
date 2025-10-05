#!/usr/bin/env python3
"""
Script to check LawBranch data and identify duplication issues.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.repositories.legal_knowledge_repository import LawSourceRepository
from app.db.database import get_db

async def check_branches():
    """Check current LawBranch data for duplication issues."""
    
    print("Checking LawBranch data for duplication issues...")
    print("=" * 60)
    
    try:
        # Get database session
        async for db in get_db():
            repo = LawSourceRepository(db)
            break
        
        # Get all law sources
        sources, total = await repo.get_law_sources()
        print(f"Found {total} law sources:")
        
        for source in sources:
            print(f"\nSource ID: {source.id}")
            print(f"Name: {source.name}")
            print(f"Type: {source.type}")
            print(f"Jurisdiction: {source.jurisdiction}")
            print(f"Created: {source.created_at}")
            
            # Get branches for this source
            branches = await repo.get_branches_by_source_id(source.id)
            print(f"Branches found: {len(branches)}")
            
            if branches:
                print("Branch details:")
                for i, branch in enumerate(branches, 1):
                    print(f"  {i}. ID: {branch.id}, Number: {branch.branch_number}, Name: {branch.branch_name[:80]}...")
                    print(f"     Order: {branch.order_index}, Created: {branch.created_at}")
                    
                    # Get chapters for this branch
                    chapters = await repo.get_chapters_by_branch_id(branch.id)
                    print(f"     Chapters: {len(chapters)}")
                    
                    if chapters:
                        for j, chapter in enumerate(chapters[:3], 1):  # Show first 3 chapters
                            print(f"        {j}. {chapter.chapter_name[:60]}...")
                        if len(chapters) > 3:
                            print(f"        ... and {len(chapters) - 3} more chapters")
            
            print("-" * 40)
            
    except Exception as e:
        print(f"Error checking branches: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_branches())

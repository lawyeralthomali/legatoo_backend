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
    
    output = []
    output.append("Checking LawBranch data for duplication issues...")
    output.append("=" * 60)
    
    try:
        # Get database session
        async for db in get_db():
            repo = LawSourceRepository(db)
            break
        
        # Get all law sources
        sources, total = await repo.get_law_sources()
        output.append(f"Found {total} law sources:")
        
        for source in sources:
            output.append(f"\nSource ID: {source.id}")
            output.append(f"Name: {source.name}")
            output.append(f"Type: {source.type}")
            output.append(f"Jurisdiction: {source.jurisdiction}")
            output.append(f"Created: {source.created_at}")
            
            # Get branches for this source
            branches = await repo.get_branches_by_source_id(source.id)
            output.append(f"Branches found: {len(branches)}")
            
            if branches:
                output.append("Branch details:")
                for i, branch in enumerate(branches, 1):
                    output.append(f"  {i}. ID: {branch.id}, Number: {branch.branch_number}")
                    output.append(f"     Name: {branch.branch_name}")
                    output.append(f"     Order: {branch.order_index}, Created: {branch.created_at}")
                    
                    # Get chapters for this branch
                    chapters = await repo.get_chapters_by_branch_id(branch.id)
                    output.append(f"     Chapters: {len(chapters)}")
                    
                    if chapters:
                        for j, chapter in enumerate(chapters[:3], 1):  # Show first 3 chapters
                            output.append(f"        {j}. {chapter.chapter_name}")
                        if len(chapters) > 3:
                            output.append(f"        ... and {len(chapters) - 3} more chapters")
            
            output.append("-" * 40)
            
        # Save output to file
        with open("branches_check_output.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))
        
        print("Branch check completed. Results saved to branches_check_output.txt")
            
    except Exception as e:
        error_msg = f"Error checking branches: {str(e)}"
        output.append(error_msg)
        print(error_msg)
        
        # Save error to file
        with open("branches_check_output.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_branches())

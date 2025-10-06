"""
Clear knowledge_documents and law_sources tables

This script will delete ALL records from:
- knowledge_documents
- law_sources (and CASCADE to law_branches, law_chapters, law_articles, knowledge_chunks)

Use this to start fresh with improved parser.
"""
import asyncio
from sqlalchemy import select, func, delete
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import (
    LawSource, LawBranch, LawChapter, LawArticle, 
    KnowledgeDocument, KnowledgeChunk
)

async def show_current_stats():
    """Show current record counts"""
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 100)
        print("CURRENT DATABASE STATISTICS")
        print("=" * 100)
        
        # Count records in each table
        tables = [
            (KnowledgeDocument, "Knowledge Documents"),
            (LawSource, "Law Sources"),
            (LawBranch, "Law Branches"),
            (LawChapter, "Law Chapters"),
            (LawArticle, "Law Articles"),
            (KnowledgeChunk, "Knowledge Chunks"),
        ]
        
        total_records = 0
        for model, name in tables:
            result = await db.execute(select(func.count()).select_from(model))
            count = result.scalar()
            total_records += count
            print(f"   {name:25s}: {count:5d} records")
        
        print(f"\n   {'TOTAL':25s}: {total_records:5d} records")
        print("=" * 100)
        
        return total_records

async def clear_tables():
    """Clear knowledge_documents and law_sources tables"""
    
    # Show current state
    print("\n🔍 Checking current database state...\n")
    total_before = await show_current_stats()
    
    if total_before == 0:
        print("\n✅ Tables are already empty. Nothing to clear.")
        return
    
    # Ask for confirmation
    print("\n" + "=" * 100)
    print("⚠️  WARNING: This will DELETE ALL records from:")
    print("=" * 100)
    print("   • knowledge_documents")
    print("   • law_sources")
    print("\n   And CASCADE DELETE all related records:")
    print("   • law_branches")
    print("   • law_chapters")
    print("   • law_articles")
    print("   • knowledge_chunks")
    print("   • case_sections (if linked)")
    print("=" * 100)
    
    confirmation = input("\n❓ Are you sure you want to continue? Type 'YES' to confirm: ")
    
    if confirmation.strip().upper() != 'YES':
        print("\n❌ Operation cancelled. No changes were made.")
        return
    
    print("\n🗑️  Starting deletion process...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # Delete in correct order (child tables first, then parents)
            # Although CASCADE should handle this, explicit deletion is clearer
            
            print("   🔹 Deleting law_articles...")
            result = await db.execute(delete(LawArticle))
            articles_deleted = result.rowcount
            print(f"      ✅ Deleted {articles_deleted} articles")
            
            print("   🔹 Deleting law_chapters...")
            result = await db.execute(delete(LawChapter))
            chapters_deleted = result.rowcount
            print(f"      ✅ Deleted {chapters_deleted} chapters")
            
            print("   🔹 Deleting law_branches...")
            result = await db.execute(delete(LawBranch))
            branches_deleted = result.rowcount
            print(f"      ✅ Deleted {branches_deleted} branches")
            
            print("   🔹 Deleting knowledge_chunks...")
            result = await db.execute(delete(KnowledgeChunk))
            chunks_deleted = result.rowcount
            print(f"      ✅ Deleted {chunks_deleted} chunks")
            
            print("   🔹 Deleting law_sources...")
            result = await db.execute(delete(LawSource))
            sources_deleted = result.rowcount
            print(f"      ✅ Deleted {sources_deleted} law sources")
            
            print("   🔹 Deleting knowledge_documents...")
            result = await db.execute(delete(KnowledgeDocument))
            docs_deleted = result.rowcount
            print(f"      ✅ Deleted {docs_deleted} knowledge documents")
            
            # Commit all deletions
            await db.commit()
            
            print("\n" + "=" * 100)
            print("✅ DELETION SUMMARY")
            print("=" * 100)
            print(f"   Knowledge Documents : {docs_deleted}")
            print(f"   Law Sources        : {sources_deleted}")
            print(f"   Law Branches       : {branches_deleted}")
            print(f"   Law Chapters       : {chapters_deleted}")
            print(f"   Law Articles       : {articles_deleted}")
            print(f"   Knowledge Chunks   : {chunks_deleted}")
            print(f"\n   TOTAL DELETED      : {docs_deleted + sources_deleted + branches_deleted + chapters_deleted + articles_deleted + chunks_deleted}")
            print("=" * 100)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error during deletion: {str(e)}")
            raise
    
    # Show final state
    print("\n🔍 Verifying final state...\n")
    total_after = await show_current_stats()
    
    if total_after == 0:
        print("\n✅ SUCCESS: All tables are now empty!")
        print("   You can now re-upload laws with the improved parser.")
    else:
        print(f"\n⚠️  Warning: {total_after} records still remain")

async def main():
    print("\n" + "=" * 100)
    print("🗑️  CLEAR LAW TABLES UTILITY")
    print("=" * 100)
    print("\nThis script will empty the following tables:")
    print("  • knowledge_documents")
    print("  • law_sources (and all related law_branches, law_chapters, law_articles)")
    print("\nUse this to start fresh after the duplicate branch fix.")
    print("=" * 100)
    
    await clear_tables()
    
    print("\n✅ Done!\n")

if __name__ == "__main__":
    asyncio.run(main())

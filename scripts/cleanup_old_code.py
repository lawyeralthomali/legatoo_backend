"""
Cleanup Script: Remove Old Code and Update to New Arabic Services

This script:
1. Updates all imports to use new Arabic services
2. Optionally deletes old service files
3. Creates backup before making changes

Usage:
    python scripts/cleanup_old_code.py --backup --delete-old
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Files to update with new imports
FILES_TO_UPDATE = [
    "app/routes/search_router.py",
    "app/routes/embedding_router.py",
]

# Old files to delete (optional)
OLD_FILES = [
    "app/services/embedding_service.py",
    "app/services/semantic_search_service.py",
]

# Import replacements
REPLACEMENTS = [
    {
        "old": "from ..services.semantic_search_service import SemanticSearchService",
        "new": "from ..services.arabic_legal_search_service import ArabicLegalSearchService as SemanticSearchService"
    },
    {
        "old": "from ..services.embedding_service import EmbeddingService",
        "new": "from ..services.arabic_legal_embedding_service import ArabicLegalEmbeddingService as EmbeddingService"
    },
    {
        "old": "search_service = SemanticSearchService(db)",
        "new": "search_service = SemanticSearchService(db, model_name='arabert', use_faiss=True)\n        await search_service.initialize()"
    },
    {
        "old": "service = EmbeddingService(db",
        "new": "service = EmbeddingService(db, model_name='arabert', use_faiss=True)\n        await service.initialize()\n        service = EmbeddingService(db"
    }
]


class CleanupManager:
    """Manages the cleanup of old code."""
    
    def __init__(self, backup: bool = True, delete_old: bool = False):
        """
        Initialize cleanup manager.
        
        Args:
            backup: Whether to create backup
            delete_old: Whether to delete old files
        """
        self.backup = backup
        self.delete_old = delete_old
        self.backup_dir = Path("cleanup_backup")
        
        if backup:
            self.backup_dir = Path(f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, file_path: str):
        """Create backup of a file."""
        if not self.backup:
            return
        
        source = Path(file_path)
        if not source.exists():
            return
        
        # Create same directory structure in backup
        relative_path = source.relative_to(Path.cwd())
        backup_file = self.backup_dir / relative_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source, backup_file)
        print(f"  ✅ Backed up: {file_path}")
    
    def update_file(self, file_path: str):
        """Update imports in a file."""
        source = Path(file_path)
        if not source.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return False
        
        print(f"\n📝 Updating: {file_path}")
        
        # Create backup
        self.create_backup(file_path)
        
        # Read file
        with open(source, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track changes
        changes_made = False
        original_content = content
        
        # Apply replacements
        for replacement in REPLACEMENTS:
            if replacement['old'] in content:
                content = content.replace(replacement['old'], replacement['new'])
                changes_made = True
                print(f"  ✓ Replaced: {replacement['old'][:60]}...")
        
        # Write back if changes were made
        if changes_made:
            with open(source, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Updated successfully")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
    
    def delete_file(self, file_path: str):
        """Delete old file."""
        source = Path(file_path)
        if not source.exists():
            print(f"  ℹ️  File not found (already deleted?): {file_path}")
            return
        
        # Create backup first
        self.create_backup(file_path)
        
        # Delete file
        source.unlink()
        print(f"  ✅ Deleted: {file_path}")
    
    def run_cleanup(self):
        """Run the complete cleanup process."""
        print("="*60)
        print("🧹 CLEANUP: Remove Old Code & Update to Arabic Services")
        print("="*60)
        print()
        
        # Step 1: Update imports in files
        print("📝 STEP 1: Updating imports...")
        print("-"*60)
        
        updated_count = 0
        for file_path in FILES_TO_UPDATE:
            if self.update_file(file_path):
                updated_count += 1
        
        print()
        print(f"✅ Updated {updated_count} files")
        print()
        
        # Step 2: Delete old files (if requested)
        if self.delete_old:
            print("🗑️  STEP 2: Deleting old files...")
            print("-"*60)
            
            for file_path in OLD_FILES:
                print(f"\n📄 {file_path}")
                self.delete_file(file_path)
            
            print()
            print(f"✅ Deleted {len(OLD_FILES)} old files")
        else:
            print("ℹ️  STEP 2: Skipping file deletion (use --delete-old to delete)")
            print()
            print("Old files that can be deleted:")
            for file_path in OLD_FILES:
                print(f"  - {file_path}")
        
        print()
        print("="*60)
        print("✅ CLEANUP COMPLETED!")
        print("="*60)
        print()
        
        if self.backup:
            print(f"📦 Backup location: {self.backup_dir}")
            print()
        
        print("📝 Summary:")
        print(f"  ✓ Files updated: {updated_count}")
        if self.delete_old:
            print(f"  ✓ Files deleted: {len(OLD_FILES)}")
        print()
        
        print("🎯 Next steps:")
        print("  1. Test the API endpoints")
        print("  2. Run: python scripts/test_arabic_search.py")
        print("  3. If everything works, you can delete the backup")
        print()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Cleanup old code and update to Arabic services')
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Create backup before making changes (default: True)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup (not recommended)'
    )
    parser.add_argument(
        '--delete-old',
        action='store_true',
        help='Delete old service files'
    )
    
    args = parser.parse_args()
    
    # Determine backup setting
    backup = not args.no_backup if args.no_backup else args.backup
    
    # Confirm deletion if requested
    if args.delete_old:
        print("⚠️  WARNING: This will delete old service files:")
        for file_path in OLD_FILES:
            print(f"  - {file_path}")
        print()
        response = input("Are you sure? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return
    
    # Run cleanup
    manager = CleanupManager(backup=backup, delete_old=args.delete_old)
    manager.run_cleanup()


if __name__ == '__main__':
    main()


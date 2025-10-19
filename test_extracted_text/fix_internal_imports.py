"""
Script to fix internal imports in services after reorganization.
"""
import re
from pathlib import Path

def fix_service_internal_imports(file_path: Path, depth: int):
    """
    Fix internal imports based on directory depth.
    
    Args:
        file_path: Path to the service file
        depth: Number of levels deep (1 for services/subdir/, 2 for services/subdir/subdir/)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        if depth == 1:
            # services/auth/, services/shared/, etc.
            # from ..config -> from ...config
            # from ..db -> from ...db
            # from ..models -> from ...models
            # from ..repositories -> from ...repositories
            # from ..schemas -> from ...schemas
            # from ..utils -> from ...utils
            # from ..services -> from ...services (for cross-service imports)
            
            replacements = {
                r'from \.\.config\.': r'from ...config.',
                r'from \.\.db\.': r'from ...db.',
                r'from \.\.models\.': r'from ...models.',
                r'from \.\.repositories\.': r'from ...repositories.',
                r'from \.\.schemas\.': r'from ...schemas.',
                r'from \.\.utils\.': r'from ...utils.',
                r'from \.\.processors\.': r'from ...processors.',
            }
        elif depth == 2:
            # services/legal/knowledge/, services/legal/search/, etc.
            # from ..config -> from ....config
            # from ..db -> from ....db
            # etc.
            
            replacements = {
                r'from \.\.config\.': r'from ....config.',
                r'from \.\.db\.': r'from ....db.',
                r'from \.\.models\.': r'from ....models.',
                r'from \.\.repositories\.': r'from ....repositories.',
                r'from \.\.schemas\.': r'from ....schemas.',
                r'from \.\.utils\.': r'from ....utils.',
                r'from \.\.processors\.': r'from ....processors.',
                
                # Cross-service imports within legal/
                r'from \.\.\.services\.': r'from ....services.',
            }
        else:
            return False
        
        # Apply replacements
        for old_pattern, new_pattern in replacements.items():
            content = re.sub(old_pattern, new_pattern, content)
        
        # Only write if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("🔧 Fixing internal imports in services...")
    print("="*60)
    
    services_dir = Path('app/services')
    updated_count = 0
    
    # Process depth-1 services (services/subdir/*.py)
    for subdir in ['auth', 'user_management', 'subscription', 'contracts', 'shared']:
        subdir_path = services_dir / subdir
        if subdir_path.exists():
            for py_file in subdir_path.glob('*.py'):
                if py_file.name != '__init__.py':
                    if fix_service_internal_imports(py_file, depth=1):
                        print(f"✅ Updated (depth=1): {py_file.relative_to(services_dir)}")
                        updated_count += 1
    
    # Process depth-2 services (services/legal/subdir/*.py)
    legal_dir = services_dir / 'legal'
    if legal_dir.exists():
        for subdir in ['knowledge', 'processing', 'search', 'analysis', 'ingestion']:
            subdir_path = legal_dir / subdir
            if subdir_path.exists():
                for py_file in subdir_path.glob('*.py'):
                    if py_file.name != '__init__.py':
                        if fix_service_internal_imports(py_file, depth=2):
                            print(f"✅ Updated (depth=2): {py_file.relative_to(services_dir)}")
                            updated_count += 1
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   ✅ Files updated: {updated_count}")
    print("="*60)

if __name__ == '__main__':
    main()


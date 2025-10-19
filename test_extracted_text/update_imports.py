"""
Script to update imports after services reorganization.
"""
import re
from pathlib import Path

# Define import replacements
IMPORT_REPLACEMENTS = {
    # Legal Knowledge Services
    r'from \.\.services\.legal_laws_service import': r'from ..services.legal.knowledge.legal_laws_service import',
    r'from \.\.services\.legal_knowledge_service import': r'from ..services.legal.knowledge.legal_knowledge_service import',
    r'from \.\.services\.legal_hierarchy_service import': r'from ..services.legal.knowledge.legal_hierarchy_service import',
    r'from \.\.services\.legal_case_service import': r'from ..services.legal.knowledge.legal_case_service import',
    
    # Legal Processing Services
    r'from \.\.services\.chunk_processing_service import': r'from ..services.legal.processing.chunk_processing_service import',
    r'from \.\.services\.document_processing_service import': r'from ..services.legal.processing.document_processing_service import',
    r'from \.\.services\.semantic_chunking_service import': r'from ..services.legal.processing.semantic_chunking_service import',
    r'from \.\.services\.arabic_legal_processor import': r'from ..services.legal.processing.arabic_legal_processor import',
    
    # Legal Search Services
    r'from \.\.services\.arabic_legal_search_service import': r'from ..services.legal.search.arabic_legal_search_service import',
    r'from \.\.services\.arabic_legal_embedding_service import': r'from ..services.legal.search.arabic_legal_embedding_service import',
    
    # Legal Analysis Services
    r'from \.\.services\.gemini_legal_analyzer import': r'from ..services.legal.analysis.gemini_legal_analyzer import',
    r'from \.\.services\.hybrid_analysis_service import': r'from ..services.legal.analysis.hybrid_analysis_service import',
    r'from \.\.services\.legal_rag_service import': r'from ..services.legal.analysis.legal_rag_service import',
    
    # Legal Ingestion Services
    r'from \.\.services\.legal_case_ingestion_service import': r'from ..services.legal.ingestion.legal_case_ingestion_service import',
    
    # User Management Services
    r'from \.\.services\.user_service import': r'from ..services.user_management.user_service import',
    r'from \.\.services\.profile_service import': r'from ..services.user_management.profile_service import',
    r'from \.\.services\.super_admin_service import': r'from ..services.user_management.super_admin_service import',
    
    # Subscription Services
    r'from \.\.services\.plan_service import': r'from ..services.subscription.plan_service import',
    r'from \.\.services\.subscription_service import': r'from ..services.subscription.subscription_service import',
    r'from \.\.services\.premium_service import': r'from ..services.subscription.premium_service import',
    
    # Contract Services
    r'from \.\.services\.contract_category_service import': r'from ..services.contracts.contract_category_service import',
    r'from \.\.services\.contract_template_service import': r'from ..services.contracts.contract_template_service import',
    r'from \.\.services\.user_contract_service import': r'from ..services.contracts.user_contract_service import',
    r'from \.\.services\.user_favorite_service import': r'from ..services.contracts.user_favorite_service import',
    
    # Shared Services
    r'from \.\.services\.embedding_service import': r'from ..services.shared.embedding_service import',
    r'from \.\.services\.rag_service import': r'from ..services.shared.rag_service import',
    r'from \.\.services\.semantic_search_service import': r'from ..services.shared.semantic_search_service import',
    
    # Auth Services
    r'from \.\.services\.auth_service import': r'from ..services.auth.auth_service import',
    r'from \.\.services\.email_service import': r'from ..services.auth.email_service import',
}

def update_file_imports(file_path: Path):
    """Update imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply all replacements
        for old_pattern, new_pattern in IMPORT_REPLACEMENTS.items():
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
    print("🔄 Updating imports after services reorganization...")
    print("="*60)
    
    # Find all Python files in app directory (excluding __pycache__)
    app_dir = Path('app')
    py_files = [f for f in app_dir.rglob('*.py') if '__pycache__' not in str(f)]
    
    updated_count = 0
    total_count = len(py_files)
    
    for file_path in py_files:
        if update_file_imports(file_path):
            print(f"✅ Updated: {file_path}")
            updated_count += 1
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   Total files scanned: {total_count}")
    print(f"   ✅ Files updated: {updated_count}")
    print(f"   ⚠️  Files unchanged: {total_count - updated_count}")
    print("="*60)

if __name__ == '__main__':
    main()


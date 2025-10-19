"""
Script to reorganize services folder structure.
"""
import shutil
from pathlib import Path

# Define the reorganization map
REORGANIZATION_MAP = {
    # Legal - Knowledge
    'legal_knowledge_service.py': 'legal/knowledge/',
    'legal_laws_service.py': 'legal/knowledge/',
    'legal_hierarchy_service.py': 'legal/knowledge/',
    'legal_case_service.py': 'legal/knowledge/',
    
    # Legal - Processing
    'chunk_processing_service.py': 'legal/processing/',
    'document_processing_service.py': 'legal/processing/',
    'semantic_chunking_service.py': 'legal/processing/',
    'arabic_legal_processor.py': 'legal/processing/',
    
    # Legal - Search
    'arabic_legal_search_service.py': 'legal/search/',
    'arabic_legal_embedding_service.py': 'legal/search/',
    
    # Legal - Analysis
    'gemini_legal_analyzer.py': 'legal/analysis/',
    'hybrid_analysis_service.py': 'legal/analysis/',
    'legal_rag_service.py': 'legal/analysis/',
    
    # Legal - Ingestion
    'legal_case_ingestion_service.py': 'legal/ingestion/',
    
    # User Management
    'user_service.py': 'user_management/',
    'profile_service.py': 'user_management/',
    'super_admin_service.py': 'user_management/',
    
    # Subscription
    'plan_service.py': 'subscription/',
    'subscription_service.py': 'subscription/',
    'premium_service.py': 'subscription/',
    
    # Contracts
    'contract_category_service.py': 'contracts/',
    'contract_template_service.py': 'contracts/',
    'user_contract_service.py': 'contracts/',
    'user_favorite_service.py': 'contracts/',
    
    # Shared (deprecated services)
    'embedding_service.py': 'shared/',
    'rag_service.py': 'shared/',
    'semantic_search_service.py': 'shared/',
}

def main():
    services_dir = Path('app/services')
    
    print("="*60)
    print("🔄 Reorganizing services folder structure...")
    print("="*60)
    
    moved_count = 0
    skipped_count = 0
    
    for filename, target_subdir in REORGANIZATION_MAP.items():
        source = services_dir / filename
        target_dir = services_dir / target_subdir
        target = target_dir / filename
        
        if source.exists():
            try:
                shutil.move(str(source), str(target))
                print(f"✅ Moved: {filename} -> {target_subdir}")
                moved_count += 1
            except Exception as e:
                print(f"❌ Failed to move {filename}: {e}")
        else:
            print(f"⚠️  Skipped (already moved or doesn't exist): {filename}")
            skipped_count += 1
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   ✅ Moved: {moved_count} files")
    print(f"   ⚠️  Skipped: {skipped_count} files")
    print("="*60)

if __name__ == '__main__':
    main()


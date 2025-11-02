"""
Phase 3 & 4 - Usage Examples

Complete examples showing how to use the new services.
Copy and adapt these examples for your use case.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.complete_legal_ai_service import CompleteLegalAIService

# ============================================================================
# EXAMPLE 1: Upload and Process a Document
# ============================================================================

async def example_upload_document(db: AsyncSession):
    """
    Upload a legal document and process it completely.
    
    Supports: PDF, DOCX, Images (OCR), TXT
    """
    service = CompleteLegalAIService(db)
    
    # Upload and process
    document = await service.upload_and_process_document(
        file_path="uploads/legal_documents/saudi_labor_law.pdf",
        original_filename="saudi_labor_law.pdf",
        title="Saudi Labor Law 2023",
        document_type="labor_law",
        language="ar",
        uploaded_by_id=1,
        notes="Official version from Ministry of Labor",
        process_immediately=True  # Process in background
    )
    
    print(f"✅ Document uploaded: ID {document.id}")
    print(f"   Title: {document.title}")
    print(f"   Status: {document.processing_status}")
    
    return document


# ============================================================================
# EXAMPLE 2: Check Processing Progress
# ============================================================================

async def example_check_progress(db: AsyncSession, document_id: int):
    """Check the processing progress of a document."""
    service = CompleteLegalAIService(db)
    
    progress = await service.get_processing_progress(document_id)
    
    print(f"📊 Processing Progress:")
    print(f"   Status: {progress['status']}")
    print(f"   Progress: {progress['progress_percentage']:.1f}%")
    print(f"   Message: {progress['message']}")
    print(f"   Chunks Processed: {progress['chunks_processed']}/{progress['total_chunks']}")
    
    return progress


# ============================================================================
# EXAMPLE 3: Semantic Search
# ============================================================================

async def example_semantic_search(db: AsyncSession):
    """
    Search for relevant legal text using semantic similarity.
    
    This uses FAISS vector search for fast, accurate results.
    """
    service = CompleteLegalAIService(db)
    
    # Search query (Arabic)
    results, query_time = await service.semantic_search(
        query="ما هي حقوق العامل في الإجازات السنوية؟",
        top_k=5,
        document_type="labor_law",
        language="ar",
        similarity_threshold=0.7
    )
    
    print(f"🔍 Search Results: Found {len(results)} results in {query_time:.2f}ms")
    print()
    
    for i, result in enumerate(results, 1):
        chunk = result['chunk']
        document = result['document']
        score = result['similarity_score']
        
        print(f"{i}. Similarity: {score:.2%}")
        print(f"   Document: {document.title}")
        if chunk.article_number:
            print(f"   Article: {chunk.article_number}")
        if chunk.section_title:
            print(f"   Section: {chunk.section_title}")
        print(f"   Content: {chunk.content[:200]}...")
        print()
    
    return results


# ============================================================================
# EXAMPLE 4: AI Case Analysis
# ============================================================================

async def example_ai_case_analysis(db: AsyncSession, case_text: str):
    """
    Find similar legal cases for AI analysis.
    
    This returns the most relevant legal chunks that can be sent to
    an AI model (ChatGPT, Claude, etc.) for case analysis.
    """
    service = CompleteLegalAIService(db)
    
    # Find similar legal precedents
    similar_cases = await service.search_for_case_analysis(
        case_text=case_text,
        top_k=5
    )
    
    print(f"🤖 AI Case Analysis: Found {len(similar_cases)} relevant legal references")
    print()
    
    # Format for AI
    context_for_ai = []
    for i, case in enumerate(similar_cases, 1):
        print(f"{i}. Relevance: {case['relevance_score']:.2%}")
        print(f"   Source: {case['source_document']}")
        if case['article_number']:
            print(f"   Article: {case['article_number']}")
        if case['reference']:
            print(f"   Reference: {case['reference']}")
        print(f"   Text: {case['legal_text'][:150]}...")
        print()
        
        context_for_ai.append({
            'relevance': case['relevance_score'],
            'legal_text': case['legal_text'],
            'article': case['article_number'],
            'source': case['source_document'],
            'reference': case['reference']
        })
    
    # Now you can send context_for_ai to your AI model
    return context_for_ai


# ============================================================================
# EXAMPLE 5: Initialize FAISS Index (First Time)
# ============================================================================

async def example_initialize_faiss(db: AsyncSession):
    """
    Initialize FAISS index from existing documents.
    
    Run this once when you first set up the system, or after
    many document deletions to rebuild the index.
    """
    service = CompleteLegalAIService(db)
    
    print("🔄 Initializing FAISS index...")
    
    # This will either load existing index or build from database
    await service.initialize_faiss_index()
    
    # Get stats
    stats = service.get_faiss_stats()
    
    print("✅ FAISS index initialized:")
    print(f"   Total vectors: {stats['total_vectors']}")
    print(f"   Dimension: {stats['dimension']}")
    print(f"   Index type: {stats['index_type']}")
    
    return stats


# ============================================================================
# EXAMPLE 6: Rebuild FAISS Index
# ============================================================================

async def example_rebuild_faiss(db: AsyncSession):
    """
    Rebuild FAISS index from scratch.
    
    Use this after:
    - Many document deletions
    - Index corruption
    - Changing embedding provider
    """
    service = CompleteLegalAIService(db)
    
    print("🔄 Rebuilding FAISS index from database...")
    
    await service.rebuild_faiss_index()
    
    stats = service.get_faiss_stats()
    
    print("✅ FAISS index rebuilt:")
    print(f"   Total vectors: {stats['total_vectors']}")
    
    return stats


# ============================================================================
# EXAMPLE 7: Process Image with OCR
# ============================================================================

async def example_process_image_ocr(db: AsyncSession):
    """
    Process an image file using OCR.
    
    Requires Tesseract OCR to be installed.
    """
    service = CompleteLegalAIService(db)
    
    # Upload image document
    document = await service.upload_and_process_document(
        file_path="uploads/scanned_document.jpg",
        original_filename="scanned_law.jpg",
        title="Scanned Legal Document",
        document_type="labor_law",
        language="ar",  # OCR will use Arabic language model
        uploaded_by_id=1,
        process_immediately=True
    )
    
    print(f"✅ Image document uploaded with OCR: ID {document.id}")
    
    return document


# ============================================================================
# EXAMPLE 8: Get System Statistics
# ============================================================================

async def example_get_statistics(db: AsyncSession):
    """Get comprehensive system statistics."""
    service = CompleteLegalAIService(db)
    
    stats = await service.get_statistics()
    
    print("📊 System Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Processing status:")
    print(f"      - Done: {stats['processing_done']}")
    print(f"      - Pending: {stats['processing_pending']}")
    print(f"      - Error: {stats['processing_error']}")
    print()
    print(f"   Documents by type:")
    for doc_type, count in stats['documents_by_type'].items():
        print(f"      - {doc_type}: {count}")
    print()
    print(f"   FAISS Index:")
    print(f"      - Total vectors: {stats['faiss_index']['total_vectors']}")
    print(f"      - Dimension: {stats['faiss_index']['dimension']}")
    print(f"      - Type: {stats['faiss_index']['index_type']}")
    print()
    print(f"   Embedding:")
    print(f"      - Provider: {stats['embedding_provider']}")
    print(f"      - Dimension: {stats['embedding_dimension']}")
    
    return stats


# ============================================================================
# EXAMPLE 9: Delete Document
# ============================================================================

async def example_delete_document(db: AsyncSession, document_id: int):
    """
    Delete a document and remove from FAISS index.
    
    This deletes:
    - Document record
    - All chunks
    - File from disk
    - Vectors from FAISS index
    """
    service = CompleteLegalAIService(db)
    
    success = await service.delete_document(document_id)
    
    if success:
        print(f"✅ Document {document_id} deleted successfully")
        print("   - Database record removed")
        print("   - Chunks removed")
        print("   - File deleted from disk")
        print("   - Vectors removed from FAISS index")
    else:
        print(f"❌ Document {document_id} not found")
    
    return success


# ============================================================================
# EXAMPLE 10: Complete End-to-End Workflow
# ============================================================================

async def example_complete_workflow(db: AsyncSession):
    """
    Complete workflow from upload to AI analysis.
    
    This demonstrates the entire process:
    1. Upload document
    2. Wait for processing
    3. Search for relevant content
    4. Analyze with AI
    """
    import asyncio
    
    service = CompleteLegalAIService(db)
    
    print("=" * 60)
    print("COMPLETE WORKFLOW EXAMPLE")
    print("=" * 60)
    print()
    
    # Step 1: Initialize FAISS (first time only)
    print("Step 1: Initialize FAISS index...")
    await service.initialize_faiss_index()
    print("✅ FAISS initialized")
    print()
    
    # Step 2: Upload document
    print("Step 2: Upload document...")
    document = await service.upload_and_process_document(
        file_path="uploads/sample_law.pdf",
        original_filename="sample_law.pdf",
        title="Sample Legal Document",
        document_type="labor_law",
        language="ar",
        uploaded_by_id=1,
        process_immediately=True
    )
    print(f"✅ Document uploaded: ID {document.id}")
    print()
    
    # Step 3: Monitor processing (in production, use webhooks/polling)
    print("Step 3: Monitoring processing...")
    while True:
        progress = await service.get_processing_progress(document.id)
        print(f"   Progress: {progress['progress_percentage']:.1f}% - {progress['message']}")
        
        if progress['status'] in ['done', 'error']:
            break
        
        await asyncio.sleep(2)  # Wait 2 seconds
    
    if progress['status'] == 'done':
        print("✅ Processing complete!")
    else:
        print("❌ Processing failed!")
        return
    print()
    
    # Step 4: Search
    print("Step 4: Semantic search...")
    results, query_time = await service.semantic_search(
        query="employee rights vacation",
        top_k=3,
        language="ar",
        similarity_threshold=0.6
    )
    print(f"✅ Found {len(results)} results in {query_time:.2f}ms")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Similarity: {result['similarity_score']:.2%}")
    print()
    
    # Step 5: AI Analysis
    print("Step 5: AI case analysis...")
    case_text = "Employee fired without justification during probation period"
    similar_cases = await service.search_for_case_analysis(
        case_text=case_text,
        top_k=3
    )
    print(f"✅ Found {len(similar_cases)} relevant legal references for AI")
    print()
    
    # Step 6: Get statistics
    print("Step 6: System statistics...")
    stats = await service.get_statistics()
    print(f"✅ Total documents: {stats['total_documents']}")
    print(f"✅ Total chunks: {stats['total_chunks']}")
    print(f"✅ FAISS vectors: {stats['faiss_index']['total_vectors']}")
    print()
    
    print("=" * 60)
    print("WORKFLOW COMPLETE!")
    print("=" * 60)


# ============================================================================
# HOW TO RUN THESE EXAMPLES
# ============================================================================

"""
To run these examples, you need a database session.

Example:

from app.db.database import get_db

async def main():
    async with get_db() as db:
        # Run example 1
        document = await example_upload_document(db)
        
        # Run example 3
        results = await example_semantic_search(db)
        
        # Run complete workflow
        await example_complete_workflow(db)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""


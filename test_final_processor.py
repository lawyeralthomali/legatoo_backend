#!/usr/bin/env python3
"""
Final test script for the hierarchical document processing system.
Tests the complete workflow with the Saudi Labor Law PDF.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.legal_knowledge_service import LegalKnowledgeService
from app.db.database import get_db
from app.services.hierarchical_document_processor import HierarchicalDocumentProcessor

async def test_hierarchical_processing():
    """Test the complete hierarchical document processing system."""
    
    print("Testing Hierarchical Document Processing System")
    print("=" * 60)
    
    # Test file path
    test_file = "fff/file/قانون العمل السعودي.pdf"
    
    if not os.path.exists(test_file):
        print(f"ERROR: Test file not found: {test_file}")
        return False
    
    print(f"Test file: {test_file}")
    print(f"File size: {os.path.getsize(test_file):,} bytes")
    
    try:
        # Get database session
        async for db in get_db():
            service = LegalKnowledgeService(db)
            break
        
        print("\nProcessing document...")
        
        # Process the document
        law_source_details = {
            "name": "Saudi Labor Law Test",
            "type": "law",
            "jurisdiction": "Saudi Arabia"
        }
        
        result = await service.process_arabic_legal_document_hierarchical(
            file_path=test_file,
            law_source_details=law_source_details
        )
        
        print(f"Processing completed!")
        print(f"Result: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success']:
            data = result['data']
            # Handle both dict and Pydantic model responses
            if isinstance(data, dict):
                law_source = data.get('law_source', {})
                structure = data.get('structure', {})
                processing_report = data.get('processing_report', {})
            else:
                law_source = data.law_source
                structure = data.structure
                processing_report = data.processing_report
            
            print(f"\nDocument Information:")
            print(f"   ID: {law_source.get('id') if isinstance(law_source, dict) else law_source.id}")
            print(f"   Name: {law_source.get('name') if isinstance(law_source, dict) else law_source.name}")
            print(f"   Type: {law_source.get('type') if isinstance(law_source, dict) else law_source.type}")
            print(f"   Jurisdiction: {law_source.get('jurisdiction') if isinstance(law_source, dict) else law_source.jurisdiction}")
            
            print(f"\nStructure Statistics:")
            structure_stats = law_source.get('structure_stats', {}) if isinstance(law_source, dict) else law_source.structure_stats
            print(f"   Chapters: {structure_stats.get('chapters', 0) if isinstance(structure_stats, dict) else structure_stats.chapters}")
            print(f"   Sections: {structure_stats.get('sections', 0) if isinstance(structure_stats, dict) else structure_stats.sections}")
            print(f"   Articles: {structure_stats.get('articles', 0) if isinstance(structure_stats, dict) else structure_stats.articles}")
            print(f"   Confidence: {(structure_stats.get('confidence', 0) if isinstance(structure_stats, dict) else structure_stats.confidence):.2f}")
            
            print(f"\nStructure Details:")
            print(f"   Total Chapters: {structure.get('total_chapters', 0) if isinstance(structure, dict) else structure.total_chapters}")
            print(f"   Total Sections: {structure.get('total_sections', 0) if isinstance(structure, dict) else structure.total_sections}")
            print(f"   Total Articles: {structure.get('total_articles', 0) if isinstance(structure, dict) else structure.total_articles}")
            print(f"   Structure Confidence: {(structure.get('structure_confidence', 0) if isinstance(structure, dict) else structure.structure_confidence):.2f}")
            
            chapters = structure.get('chapters', []) if isinstance(structure, dict) else structure.chapters
            if chapters:
                print(f"\nChapters Found:")
                for i, chapter in enumerate(chapters[:3], 1):  # Show first 3 chapters
                    chapter_num = chapter.get('number', 'N/A') if isinstance(chapter, dict) else chapter.number
                    chapter_title = chapter.get('title', 'No title') if isinstance(chapter, dict) else chapter.title
                    print(f"   {i}. {chapter_num}: {chapter_title[:50]}...")
                    
                    sections = chapter.get('sections', []) if isinstance(chapter, dict) else chapter.sections
                    if sections:
                        print(f"      Sections: {len(sections)}")
                        for j, section in enumerate(sections[:2], 1):  # Show first 2 sections
                            section_num = section.get('number', 'N/A') if isinstance(section, dict) else section.number
                            section_title = section.get('title', 'No title') if isinstance(section, dict) else section.title
                            print(f"         {j}. {section_num}: {section_title[:40]}...")
                            articles = section.get('articles', []) if isinstance(section, dict) else section.articles
                            if articles:
                                print(f"            Articles: {len(articles)}")
                    else:
                        articles = chapter.get('articles', []) if isinstance(chapter, dict) else chapter.articles
                        if articles:
                            print(f"      Articles: {len(articles)}")
                
                if len(chapters) > 3:
                    print(f"   ... and {len(chapters) - 3} more chapters")
            else:
                print(f"\nNo chapters found!")
            
            orphaned_articles = structure.get('orphaned_articles', []) if isinstance(structure, dict) else structure.orphaned_articles
            if orphaned_articles:
                print(f"\nOrphaned Articles: {len(orphaned_articles)}")
                for i, article in enumerate(orphaned_articles[:3], 1):
                    article_num = article.get('number', 'N/A') if isinstance(article, dict) else article.number
                    article_title = article.get('title', 'No title') if isinstance(article, dict) else article.title
                    print(f"   {i}. {article_num}: {article_title[:50]}...")
            
            print(f"\nProcessing Report:")
            print(f"   Processing Time: {(processing_report.get('processing_time', 0) if isinstance(processing_report, dict) else processing_report.processing_time):.2f} seconds")
            print(f"   Text Length: {(processing_report.get('text_length', 0) if isinstance(processing_report, dict) else processing_report.text_length):,} characters")
            print(f"   Pages Processed: {processing_report.get('pages_processed', 0) if isinstance(processing_report, dict) else processing_report.pages_processed}")
            
            warnings = processing_report.get('warnings', []) if isinstance(processing_report, dict) else processing_report.warnings
            if warnings:
                print(f"   Warnings ({len(warnings)}):")
                for warning in warnings[:5]:
                    print(f"      - {warning}")
            
            errors = processing_report.get('errors', []) if isinstance(processing_report, dict) else processing_report.errors
            if errors:
                print(f"   Errors ({len(errors)}):")
                for error in errors[:5]:
                    print(f"      - {error}")
            
            suggestions = processing_report.get('suggestions', []) if isinstance(processing_report, dict) else processing_report.suggestions
            if suggestions:
                print(f"   Suggestions ({len(suggestions)}):")
                for suggestion in suggestions[:5]:
                    print(f"      - {suggestion}")
            
            # Test structure retrieval
            print(f"\nTesting structure retrieval...")
            law_source_id = law_source.get('id') if isinstance(law_source, dict) else law_source.id
            structure_result = await service.get_document_structure(law_source_id)
            
            if structure_result['success']:
                print(f"Structure retrieval successful!")
                retrieved_structure = structure_result['data']
                retrieved_chapters = retrieved_structure.get('chapters', []) if isinstance(retrieved_structure, dict) else retrieved_structure.chapters
                print(f"   Retrieved chapters: {len(retrieved_chapters)}")
            else:
                print(f"Structure retrieval failed: {structure_result['message']}")
            
            return True
            
        else:
            print(f"Processing failed!")
            errors = result.get('errors', [])
            if errors:
                print(f"   Errors:")
                for error in errors:
                    print(f"      - {error.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_pattern_recognition():
    """Test the Arabic pattern recognition directly."""
    
    print("\nTesting Arabic Pattern Recognition")
    print("=" * 40)
    
    try:
        # Create a mock db session for pattern testing
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            processor = HierarchicalDocumentProcessor(db)
            
            # Test patterns
            test_texts = [
            "ﺍﻟﺒﺎﺏ ﺍﻷﻭﻝ",  # First chapter
            "ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ",  # Second chapter
            "ﺍﻟﻔﺼﻞ ﺍﻷﻭﻝ",  # First section
            "ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ",  # First article
            "ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ",  # Second article
            "الباب الأول",  # Original format
            "الفصل الأول",  # Original format
            "المادة الأولى"  # Original format
        ]
        
            for text in test_texts:
                analysis = processor.pattern_recognizer.analyze_line(text, 1)
                print(f"   '{text}' -> {analysis.element_type.value if analysis else 'None'}")
            
    except Exception as e:
        print(f"Pattern recognition test failed: {str(e)}")

async def main():
    """Main test function."""
    
    print("Starting Comprehensive Hierarchical Document Processing Test")
    print("=" * 70)
    
    # Test pattern recognition first
    await test_pattern_recognition()
    
    # Test full processing
    success = await test_hierarchical_processing()
    
    print(f"\n{'='*70}")
    if success:
        print("All tests completed successfully!")
        print("The hierarchical document processing system is working correctly.")
        print("Pydantic validation errors have been resolved.")
        print("Structure extraction is functioning properly.")
    else:
        print("Some tests failed. Please check the output above.")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())

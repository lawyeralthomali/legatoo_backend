#!/usr/bin/env python3
"""
Complete Workflow - Upload → Embed → Test
==================================================

This script handles the complete workflow for uploading laws and cases,
generating embeddings, and testing search accuracy.

Steps:
1. Upload laws from data_set/files/
2. Upload cases from data_set/cases/
3. Generate embeddings using Arabic BERT
4. Test search accuracy with known queries
5. Generate accuracy report

Usage:
    python COMPLETE_WORKFLOW.py
"""

import os
import sys
import asyncio
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService
from app.services.arabic_legal_search_service import ArabicLegalSearchService
from sqlalchemy import select, func
from app.models.legal_knowledge import KnowledgeChunk, LawArticle, LegalCase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteWorkflow:
    """Handles the complete workflow from upload to testing."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results = {
            'laws_uploaded': 0,
            'cases_uploaded': 0,
            'embeddings_generated': 0,
            'search_tests': [],
            'overall_accuracy': 0.0
        }
    
    async def step1_upload_laws(self) -> bool:
        """Step 1: Upload laws using batch script."""
        logger.info("\n" + "="*80)
        logger.info("📚 STEP 1: Uploading Laws")
        logger.info("="*80)
        
        try:
            # Run batch upload script
            import subprocess
            result = subprocess.run(
                [sys.executable, "data_set/batch_upload_laws.py"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.info("✅ Laws uploaded successfully")
                # Parse summary file
                summary_file = Path("data_set/batch_laws_upload_summary.json")
                if summary_file.exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                        self.results['laws_uploaded'] = summary.get('total_laws', 0)
                        logger.info(f"   Total laws: {self.results['laws_uploaded']}")
                return True
            else:
                logger.error(f"❌ Failed to upload laws")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ Error uploading laws: {str(e)}")
            return False
    
    async def step2_upload_cases(self) -> bool:
        """Step 2: Upload cases using batch script."""
        logger.info("\n" + "="*80)
        logger.info("⚖️  STEP 2: Uploading Cases")
        logger.info("="*80)
        
        try:
            # Run batch upload script
            import subprocess
            result = subprocess.run(
                [sys.executable, "data_set/batch_upload_cases.py"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.info("✅ Cases uploaded successfully")
                # Parse summary file
                summary_file = Path("data_set/batch_cases_upload_summary.json")
                if summary_file.exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                        self.results['cases_uploaded'] = summary.get('total_cases', 0)
                        logger.info(f"   Total cases: {self.results['cases_uploaded']}")
                return True
            else:
                logger.error(f"❌ Failed to upload cases")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ Error uploading cases: {str(e)}")
            return False
    
    async def step3_generate_embeddings(self) -> bool:
        """Step 3: Generate embeddings for all chunks."""
        logger.info("\n" + "="*80)
        logger.info("🤖 STEP 3: Generating Embeddings with Arabic BERT")
        logger.info("="*80)
        
        try:
            async with AsyncSessionLocal() as db:
                # Count chunks without embeddings
                result = await db.execute(
                    select(func.count(KnowledgeChunk.id))
                    .where(KnowledgeChunk.embedding_vector.is_(None))
                )
                chunks_to_process = result.scalar()
                
                if chunks_to_process == 0:
                    logger.info("✅ All chunks already have embeddings")
                    return True
                
                logger.info(f"📊 Chunks to process: {chunks_to_process}")
                
                # Get all chunk IDs
                result = await db.execute(
                    select(KnowledgeChunk.id)
                    .where(KnowledgeChunk.embedding_vector.is_(None))
                )
                chunk_ids = [row[0] for row in result.all()]
                
                # Initialize embedding service
                logger.info("🔧 Initializing Arabic BERT model...")
                embedding_service = ArabicLegalEmbeddingService(
                    db=db,
                    model_name='arabert',
                    use_faiss=True
                )
                embedding_service.initialize_model()
                
                # Generate embeddings
                logger.info("⚡ Generating embeddings...")
                start_time = time.time()
                
                result = await embedding_service.generate_batch_embeddings(
                    chunk_ids=chunk_ids,
                    overwrite=False
                )
                
                elapsed_time = time.time() - start_time
                
                if result['success']:
                    self.results['embeddings_generated'] = result['processed_chunks']
                    logger.info(f"✅ Generated {result['processed_chunks']} embeddings")
                    logger.info(f"⏱️  Time: {elapsed_time:.1f}s")
                    logger.info(f"⚡ Speed: {result.get('speed', 'N/A')}")
                    return True
                else:
                    logger.error(f"❌ Embedding generation failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def step4_test_accuracy(self) -> bool:
        """Step 4: Test search accuracy with known queries."""
        logger.info("\n" + "="*80)
        logger.info("🧪 STEP 4: Testing Search Accuracy")
        logger.info("="*80)
        
        # Define test queries with expected results
        test_queries = [
            {
                'query': 'عقوبة تزوير الطوابع',
                'expected_keywords': ['تزوير', 'طابع', 'عقوبة'],
                'expected_law_contains': 'التزوير',
                'min_similarity': 0.75
            },
            {
                'query': 'خاتم الدولة',
                'expected_keywords': ['خاتم', 'الدولة'],
                'expected_law_contains': 'التزوير',
                'min_similarity': 0.70
            },
            {
                'query': 'عقوبة تزوير المحررات',
                'expected_keywords': ['تزوير', 'محرر'],
                'expected_law_contains': 'التزوير',
                'min_similarity': 0.70
            }
        ]
        
        try:
            async with AsyncSessionLocal() as db:
                search_service = ArabicLegalSearchService(
                    db=db,
                    model_name='arabert',
                    use_faiss=True
                )
                search_service.embedding_service.initialize_model()
                
                passed_tests = 0
                total_tests = len(test_queries)
                
                for i, test in enumerate(test_queries, 1):
                    logger.info(f"\n📋 Test {i}/{total_tests}: {test['query']}")
                    logger.info("-"*80)
                    
                    # Perform search
                    results = await search_service.find_similar_laws(
                        query=test['query'],
                        top_k=3,
                        threshold=0.3  # Low threshold to see all results
                    )
                    
                    if not results:
                        logger.error(f"❌ No results returned")
                        self.results['search_tests'].append({
                            'query': test['query'],
                            'passed': False,
                            'reason': 'No results'
                        })
                        continue
                    
                    # Check top result
                    top_result = results[0]
                    similarity = top_result['similarity']
                    content = top_result['content'].lower()
                    
                    # Validate
                    checks = {
                        'similarity': similarity >= test['min_similarity'],
                        'keywords': any(kw in content for kw in test['expected_keywords']),
                        'law': test['expected_law_contains'].lower() in top_result.get('law_metadata', {}).get('law_name', '').lower() if 'law_metadata' in top_result else False
                    }
                    
                    passed = all(checks.values())
                    
                    if passed:
                        logger.info(f"✅ PASSED")
                        passed_tests += 1
                    else:
                        logger.warning(f"⚠️  FAILED")
                    
                    logger.info(f"   Similarity: {similarity:.4f} (min: {test['min_similarity']})")
                    logger.info(f"   Keywords found: {checks['keywords']}")
                    logger.info(f"   Correct law: {checks['law']}")
                    logger.info(f"   Content preview: {top_result['content'][:150]}...")
                    
                    self.results['search_tests'].append({
                        'query': test['query'],
                        'passed': passed,
                        'similarity': similarity,
                        'checks': checks,
                        'top_result': {
                            'chunk_id': top_result['chunk_id'],
                            'content': top_result['content'][:200],
                            'law_name': top_result.get('law_metadata', {}).get('law_name', 'N/A')
                        }
                    })
                
                # Calculate accuracy
                accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                self.results['overall_accuracy'] = accuracy
                
                logger.info("\n" + "="*80)
                logger.info(f"📊 ACCURACY RESULTS")
                logger.info("="*80)
                logger.info(f"✅ Passed: {passed_tests}/{total_tests}")
                logger.info(f"📈 Accuracy: {accuracy:.1f}%")
                
                if accuracy >= 99:
                    logger.info("🎉 EXCELLENT! 99%+ accuracy achieved!")
                    return True
                elif accuracy >= 90:
                    logger.info("✅ GOOD! 90%+ accuracy achieved")
                    return True
                elif accuracy >= 70:
                    logger.warning("⚠️  ACCEPTABLE but could be better")
                    return True
                else:
                    logger.error("❌ POOR accuracy - needs improvement")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error testing accuracy: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def run_complete_workflow(self) -> None:
        """Run the complete workflow."""
        logger.info("\n" + "="*100)
        logger.info("🚀 STARTING COMPLETE WORKFLOW")
        logger.info("="*100)
        
        start_time = time.time()
        
        # Step 1: Upload Laws
        if not await self.step1_upload_laws():
            logger.error("❌ Workflow failed at Step 1 (Upload Laws)")
            return
        
        # Step 2: Upload Cases
        if not await self.step2_upload_cases():
            logger.error("❌ Workflow failed at Step 2 (Upload Cases)")
            return
        
        # Step 3: Generate Embeddings
        if not await self.step3_generate_embeddings():
            logger.error("❌ Workflow failed at Step 3 (Generate Embeddings)")
            return
        
        # Step 4: Test Accuracy
        if not await self.step4_test_accuracy():
            logger.warning("⚠️  Accuracy tests did not pass all checks")
        
        # Print final summary
        elapsed_time = time.time() - start_time
        
        logger.info("\n" + "="*100)
        logger.info("📊 WORKFLOW COMPLETE - FINAL SUMMARY")
        logger.info("="*100)
        logger.info(f"📚 Laws uploaded: {self.results['laws_uploaded']}")
        logger.info(f"⚖️  Cases uploaded: {self.results['cases_uploaded']}")
        logger.info(f"🤖 Embeddings generated: {self.results['embeddings_generated']}")
        logger.info(f"📈 Overall accuracy: {self.results['overall_accuracy']:.1f}%")
        logger.info(f"⏱️  Total time: {elapsed_time:.1f}s")
        logger.info("="*100)
        
        # Save results
        results_file = Path("workflow_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n📄 Results saved to: {results_file}")
        
        if self.results['overall_accuracy'] >= 99:
            logger.info("\n🎉 SUCCESS! System is production-ready with 99%+ accuracy!")
        elif self.results['overall_accuracy'] >= 90:
            logger.info("\n✅ GOOD! System is ready with 90%+ accuracy")
        else:
            logger.warning("\n⚠️  System needs tuning to reach 99% accuracy")


async def main():
    """Main entry point."""
    try:
        workflow = CompleteWorkflow()
        await workflow.run_complete_workflow()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Workflow interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


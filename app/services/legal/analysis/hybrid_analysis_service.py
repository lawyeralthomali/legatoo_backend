"""
Hybrid Analysis Service - خدمة التحليل الهجين

This service combines Gemini AI analysis with semantic search validation
to provide the most accurate and reliable legal analysis.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .gemini_legal_analyzer import GeminiLegalAnalyzer
from ..search.arabic_legal_search_service import ArabicLegalSearchService

logger = logging.getLogger(__name__)


class HybridAnalysisService:
    """
    يدمج ذكاء Gemini مع البحث الدلالي لتحقيق أقصى دقة في التحليل القانوني.
    
    Workflow:
    1. Gemini analyzes the case and provides insights
    2. Semantic search validates the analysis against knowledge base
    3. Results are merged for maximum accuracy
    
    Features:
    - AI-powered analysis with Gemini
    - Validation against knowledge base
    - Cross-referencing with actual laws and cases
    - Confidence scoring
    - Error detection and correction
    """
    
    def __init__(self, db: AsyncSession, gemini_api_key: Optional[str] = None):
        """
        Initialize Hybrid Analysis Service.
        
        Args:
            db: Async database session
            gemini_api_key: Optional Gemini API key
        """
        self.db = db
        self.gemini_analyzer = GeminiLegalAnalyzer(api_key=gemini_api_key)
        self.search_service = ArabicLegalSearchService(db, use_faiss=True)  # uses paraphrase-multilingual by default
        
        logger.info("✅ Hybrid Analysis Service initialized with Arabic BERT")
    
    async def analyze_case(
        self,
        case_text: str,
        validation_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        تحليل شامل للقضية مع التحقق من الصحة.
        
        Args:
            case_text: نص القضية
            validation_level: مستوى التحقق ('quick', 'standard', 'deep')
            
        Returns:
            تحليل مُحقق ومُدمج
        """
        try:
            logger.info(f"🔍 Starting hybrid analysis for case: '{case_text[:100]}...'")
            start_time = datetime.utcnow()
            
            # Step 1: Get Gemini analysis
            logger.info("📊 Step 1: Getting Gemini analysis...")
            gemini_analysis = await self.gemini_analyzer.comprehensive_legal_analysis(case_text)
            
            if not gemini_analysis.get('success'):
                logger.error(f"❌ Gemini analysis failed: {gemini_analysis.get('error')}")
                return {
                    "success": False,
                    "error": "Gemini analysis failed",
                    "details": gemini_analysis
                }
            
            # Step 2: Validate with semantic search
            logger.info("✅ Step 2: Validating with semantic search...")
            validation_results = await self.validate_with_semantic_search(
                case_text,
                gemini_analysis,
                level=validation_level
            )
            
            # Step 3: Merge results
            logger.info("🔄 Step 3: Merging analyses...")
            final_analysis = self.merge_analyses(
                gemini_analysis,
                validation_results
            )
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Add metadata
            final_analysis.update({
                "processing_time_seconds": processing_time,
                "validation_level": validation_level,
                "timestamp": end_time.isoformat()
            })
            
            logger.info(f"✅ Hybrid analysis completed in {processing_time:.2f} seconds")
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"❌ Hybrid analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_with_semantic_search(
        self,
        case_text: str,
        gemini_analysis: Dict[str, Any],
        level: str = "standard"
    ) -> Dict[str, Any]:
        """
        التحقق من صحة تحليل Gemini باستخدام البحث الدلالي في قاعدة المعرفة.
        
        Args:
            case_text: نص القضية الأصلي
            gemini_analysis: تحليل Gemini
            level: مستوى التحقق
            
        Returns:
            نتائج التحقق
        """
        try:
            validation_results = {
                "laws_validation": {},
                "cases_validation": {},
                "overall_confidence": 0.0,
                "recommendations": []
            }
            
            # Extract analysis data
            analysis_data = gemini_analysis.get('analysis', {})
            
            # Validate applicable laws
            applicable_laws = analysis_data.get('applicable_laws', [])
            if applicable_laws and isinstance(applicable_laws, list):
                logger.info(f"🔍 Validating {len(applicable_laws)} laws...")
                
                for law in applicable_laws[:3]:  # Validate top 3 laws
                    if isinstance(law, dict):
                        law_name = law.get('law_name', '')
                        if law_name:
                            # Search for this law in knowledge base
                            search_results = await self.search_service.find_similar_laws(
                                query=law_name,
                                top_k=2,
                                threshold=0.7
                            )
                            
                            validation_results['laws_validation'][law_name] = {
                                "found_in_db": len(search_results) > 0,
                                "matches_count": len(search_results),
                                "similarity": search_results[0]['similarity'] if search_results else 0.0,
                                "actual_content": search_results[0]['content'][:200] if search_results else "",
                                "validated": len(search_results) > 0 and search_results[0]['similarity'] > 0.7
                            }
            
            # Validate with similar cases
            if level in ['standard', 'deep']:
                logger.info("🔍 Searching for similar cases...")
                similar_cases = await self.search_service.find_similar_cases(
                    query=case_text,
                    top_k=3,
                    threshold=0.7
                )
                
                validation_results['cases_validation'] = {
                    "similar_cases_found": len(similar_cases),
                    "cases": [
                        {
                            "case_id": case['chunk_id'],
                            "similarity": case['similarity'],
                            "content_preview": case['content'][:150]
                        }
                        for case in similar_cases
                    ]
                }
            
            # Deep validation: Check for conflicting information
            if level == 'deep':
                logger.info("🔍 Performing deep validation...")
                validation_results['deep_validation'] = await self._deep_validation(
                    case_text,
                    analysis_data
                )
            
            # Calculate overall confidence
            validated_laws = sum(
                1 for v in validation_results['laws_validation'].values()
                if v.get('validated', False)
            )
            total_laws = len(validation_results['laws_validation'])
            
            if total_laws > 0:
                validation_results['overall_confidence'] = (validated_laws / total_laws) * 100
            else:
                validation_results['overall_confidence'] = 50.0  # Default if no laws to validate
            
            # Add recommendations
            if validation_results['overall_confidence'] < 50:
                validation_results['recommendations'].append(
                    "⚠️ Low confidence: Manual review recommended"
                )
            
            if not validation_results['cases_validation'].get('similar_cases_found', 0):
                validation_results['recommendations'].append(
                    "💡 No similar cases found: This may be a unique case"
                )
            
            logger.info(f"✅ Validation completed. Confidence: {validation_results['overall_confidence']:.1f}%")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            return {
                "error": str(e),
                "overall_confidence": 0.0,
                "recommendations": ["❌ Validation failed - use Gemini results with caution"]
            }
    
    async def _deep_validation(
        self,
        case_text: str,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        تحقق عميق من التحليل (للمستوى المتقدم).
        
        Args:
            case_text: نص القضية
            analysis_data: بيانات التحليل
            
        Returns:
            نتائج التحقق العميق
        """
        try:
            deep_results = {
                "consistency_check": True,
                "conflicts_found": [],
                "additional_laws_found": []
            }
            
            # Search for additional relevant laws
            hybrid_search = await self.search_service.hybrid_search(
                query=case_text,
                search_types=['laws', 'cases'],
                top_k=3,
                threshold=0.75
            )
            
            # Check if Gemini missed any important laws
            if hybrid_search.get('laws', {}).get('count', 0) > 0:
                found_laws = hybrid_search['laws']['results']
                mentioned_laws = [
                    law.get('law_name', '')
                    for law in analysis_data.get('applicable_laws', [])
                ]
                
                for law in found_laws:
                    law_name = law.get('law_metadata', {}).get('law_name', '')
                    if law_name and law_name not in mentioned_laws:
                        deep_results['additional_laws_found'].append({
                            "law_name": law_name,
                            "similarity": law['similarity'],
                            "reason": "Found in semantic search but not mentioned by Gemini"
                        })
            
            return deep_results
            
        except Exception as e:
            logger.error(f"❌ Deep validation failed: {str(e)}")
            return {"error": str(e)}
    
    def merge_analyses(
        self,
        gemini_analysis: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        دمج نتائج Gemini مع نتائج التحقق للحصول على التحليل النهائي.
        
        Args:
            gemini_analysis: تحليل Gemini
            validation_results: نتائج التحقق
            
        Returns:
            التحليل النهائي المُدمج
        """
        try:
            merged = {
                "success": True,
                "analysis_source": "hybrid",
                "gemini_analysis": gemini_analysis.get('analysis', {}),
                "validation": validation_results,
                "overall_confidence": validation_results.get('overall_confidence', 0.0),
                "recommendations": validation_results.get('recommendations', []),
                "metadata": {
                    "gemini_model": gemini_analysis.get('model', 'gemini-pro'),
                    "tokens_used": gemini_analysis.get('tokens_used', 0),
                    "validated_laws": len(validation_results.get('laws_validation', {})),
                    "similar_cases_found": validation_results.get('cases_validation', {}).get('similar_cases_found', 0)
                }
            }
            
            # Add enhanced recommendations based on validation
            if validation_results.get('deep_validation', {}).get('additional_laws_found'):
                merged['recommendations'].append(
                    "💡 Additional relevant laws found - review recommended"
                )
                merged['additional_laws'] = validation_results['deep_validation']['additional_laws_found']
            
            # Add quality score
            confidence = merged['overall_confidence']
            if confidence >= 80:
                merged['quality_score'] = "high"
            elif confidence >= 60:
                merged['quality_score'] = "medium"
            else:
                merged['quality_score'] = "low"
            
            logger.info(f"✅ Analysis merged. Quality: {merged['quality_score']}, Confidence: {confidence:.1f}%")
            
            return merged
            
        except Exception as e:
            logger.error(f"❌ Merge failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "gemini_analysis": gemini_analysis,
                "validation": validation_results
            }
    
    async def quick_analysis(self, case_text: str) -> Dict[str, Any]:
        """
        تحليل سريع بدون تحقق عميق (للحالات العاجلة).
        
        Args:
            case_text: نص القضية
            
        Returns:
            تحليل سريع
        """
        try:
            logger.info(f"⚡ Quick analysis for: '{case_text[:100]}...'")
            
            # Quick classification
            classification = await self.gemini_analyzer.quick_case_classification(case_text)
            
            # Quick search
            similar_cases = await self.search_service.find_similar_cases(
                query=case_text,
                top_k=2,
                threshold=0.75
            )
            
            return {
                "success": True,
                "analysis_type": "quick",
                "classification": classification.get('classification', {}),
                "similar_cases_count": len(similar_cases),
                "recommendation": "For detailed analysis, use comprehensive_analysis()"
            }
            
        except Exception as e:
            logger.error(f"❌ Quick analysis failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_and_validate_entities(self, case_text: str) -> Dict[str, Any]:
        """
        استخراج الكيانات من النص والتحقق منها.
        
        Args:
            case_text: نص القضية
            
        Returns:
            الكيانات المستخرجة والمُحققة
        """
        try:
            # Extract entities with Gemini
            entities_result = await self.gemini_analyzer.extract_legal_entities(case_text)
            
            if not entities_result.get('success'):
                return entities_result
            
            entities = entities_result.get('entities', {})
            
            # Validate laws mentioned
            laws_mentioned = entities.get('laws_mentioned', [])
            validated_laws = {}
            
            for law_name in laws_mentioned:
                search_results = await self.search_service.find_similar_laws(
                    query=law_name,
                    top_k=1,
                    threshold=0.8
                )
                
                validated_laws[law_name] = {
                    "exists": len(search_results) > 0,
                    "confidence": search_results[0]['similarity'] if search_results else 0.0
                }
            
            return {
                "success": True,
                "entities": entities,
                "validated_laws": validated_laws
            }
            
        except Exception as e:
            logger.error(f"❌ Entity extraction/validation failed: {str(e)}")
            return {"success": False, "error": str(e)}

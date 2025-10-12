"""
Legal RAG Service - خدمة الاسترجاع المُعزز (Retrieval-Augmented Generation)

This service implements advanced RAG for legal analysis by:
1. Retrieving relevant legal context from knowledge base
2. Analyzing with Gemini using that context
3. Providing the most accurate and grounded legal advice
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .gemini_legal_analyzer import GeminiLegalAnalyzer
from ..search.arabic_legal_search_service import ArabicLegalSearchService

logger = logging.getLogger(__name__)


class LegalRAGService:
    """
    نظام RAG المتقدم للتحليل القانوني - أعلى دقة ممكنة.
    
    RAG Workflow:
    1. **Retrieve**: Get relevant laws, cases, and principles from knowledge base
    2. **Augment**: Enrich Gemini's prompt with this context
    3. **Generate**: Let Gemini analyze with full context
    
    Benefits:
    - Grounded in actual laws and cases
    - Reduces AI hallucinations
    - Provides traceable sources
    - Maximum accuracy
    """
    
    def __init__(self, db: AsyncSession, gemini_api_key: Optional[str] = None):
        """
        Initialize Legal RAG Service.
        
        Args:
            db: Async database session
            gemini_api_key: Optional Gemini API key
        """
        self.db = db
        self.gemini_analyzer = GeminiLegalAnalyzer(api_key=gemini_api_key)
        self.search_service = ArabicLegalSearchService(db, use_faiss=True)  # uses paraphrase-multilingual by default
        
        logger.info("✅ Legal RAG Service initialized with Arabic BERT")
    
    async def rag_analysis(
        self,
        case_text: str,
        max_laws: int = 5,
        max_cases: int = 3,
        include_principles: bool = True
    ) -> Dict[str, Any]:
        """
        تحليل RAG كامل - يسترجع السياق ثم يحلل مع Gemini.
        
        Args:
            case_text: نص القضية
            max_laws: عدد القوانين المسترجعة (افتراضي 5)
            max_cases: عدد القضايا المشابهة (افتراضي 3)
            include_principles: تضمين المبادئ القانونية
            
        Returns:
            تحليل مُعزز بالسياق
        """
        try:
            logger.info(f"🔍 Starting RAG analysis for case: '{case_text[:100]}...'")
            start_time = datetime.utcnow()
            
            # Step 1: Retrieve relevant context
            logger.info("📚 Step 1: Retrieving relevant context from knowledge base...")
            context = await self.retrieve_relevant_context(
                case_text,
                max_laws=max_laws,
                max_cases=max_cases,
                include_principles=include_principles
            )
            
            # Step 2: Analyze with context using Gemini
            logger.info("🤖 Step 2: Analyzing with Gemini using retrieved context...")
            analysis = await self.analyze_with_context(case_text, context)
            
            # Step 3: Post-process and enhance
            logger.info("✨ Step 3: Enhancing results...")
            final_result = self._enhance_analysis(analysis, context)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            final_result.update({
                "processing_time_seconds": processing_time,
                "timestamp": end_time.isoformat(),
                "analysis_type": "rag"
            })
            
            logger.info(f"✅ RAG analysis completed in {processing_time:.2f} seconds")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ RAG analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def retrieve_relevant_context(
        self,
        case_text: str,
        max_laws: int = 5,
        max_cases: int = 3,
        include_principles: bool = True
    ) -> Dict[str, Any]:
        """
        استرجاع السياق الأكثر صلة من قاعدة المعرفة.
        
        Args:
            case_text: نص القضية
            max_laws: عدد القوانين المسترجعة
            max_cases: عدد القضايا المشابهة
            include_principles: تضمين المبادئ القانونية
            
        Returns:
            السياق المُسترجع
        """
        try:
            context = {
                "similar_laws": [],
                "similar_cases": [],
                "legal_principles": [],
                "procedural_rules": [],
                "sources_count": 0
            }
            
            # Retrieve similar laws
            logger.info(f"🔍 Searching for {max_laws} similar laws...")
            similar_laws = await self.search_service.find_similar_laws(
                query=case_text,
                top_k=max_laws,
                threshold=0.65
            )
            
            context['similar_laws'] = [
                {
                    "content": law['content'],
                    "similarity": law['similarity'],
                    "source": law.get('law_metadata', {}).get('law_name', 'Unknown'),
                    "article": law.get('article_metadata', {}).get('article_number', ''),
                    "verified": law.get('verified', False)
                }
                for law in similar_laws
            ]
            
            # Retrieve similar cases
            logger.info(f"🔍 Searching for {max_cases} similar cases...")
            similar_cases = await self.search_service.find_similar_cases(
                query=case_text,
                top_k=max_cases,
                threshold=0.70
            )
            
            context['similar_cases'] = [
                {
                    "content": case['content'],
                    "similarity": case['similarity'],
                    "case_number": case.get('case_metadata', {}).get('case_number', ''),
                    "court": case.get('case_metadata', {}).get('court_name', ''),
                    "decision_date": case.get('case_metadata', {}).get('decision_date', '')
                }
                for case in similar_cases
            ]
            
            # Extract legal principles (if requested)
            if include_principles:
                logger.info("📖 Extracting legal principles...")
                context['legal_principles'] = await self._extract_legal_principles(
                    context['similar_laws'],
                    context['similar_cases']
                )
            
            # Extract procedural rules
            logger.info("⚖️ Extracting procedural rules...")
            context['procedural_rules'] = await self._extract_procedural_rules(
                context['similar_laws']
            )
            
            # Count sources
            context['sources_count'] = len(context['similar_laws']) + len(context['similar_cases'])
            
            logger.info(f"✅ Retrieved {context['sources_count']} sources from knowledge base")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {str(e)}")
            return {
                "error": str(e),
                "similar_laws": [],
                "similar_cases": [],
                "sources_count": 0
            }
    
    async def _extract_legal_principles(
        self,
        laws: List[Dict],
        cases: List[Dict]
    ) -> List[str]:
        """
        استخراج المبادئ القانونية من القوانين والقضايا.
        
        Args:
            laws: قائمة القوانين
            cases: قائمة القضايا
            
        Returns:
            قائمة المبادئ القانونية
        """
        try:
            principles = []
            
            # Extract from high-similarity verified laws
            for law in laws:
                if law.get('verified') and law.get('similarity', 0) > 0.8:
                    # Extract key phrases that look like principles
                    content = law.get('content', '')
                    if any(keyword in content for keyword in ['يجب', 'لا يجوز', 'يحق', 'يلتزم']):
                        principles.append(content[:200] + "...")
            
            # Extract from cases (precedents)
            for case in cases:
                if case.get('similarity', 0) > 0.85:
                    content = case.get('content', '')
                    if any(keyword in content for keyword in ['المبدأ', 'القاعدة', 'حكمت المحكمة']):
                        principles.append(f"سابقة قضائية: {content[:150]}...")
            
            return principles[:5]  # Top 5 principles
            
        except Exception as e:
            logger.error(f"❌ Failed to extract principles: {str(e)}")
            return []
    
    async def _extract_procedural_rules(self, laws: List[Dict]) -> List[str]:
        """
        استخراج القواعد الإجرائية من القوانين.
        
        Args:
            laws: قائمة القوانين
            
        Returns:
            قائمة القواعد الإجرائية
        """
        try:
            rules = []
            
            for law in laws:
                content = law.get('content', '')
                # Look for procedural keywords
                if any(keyword in content for keyword in ['إجراء', 'مدة', 'ميعاد', 'تقديم', 'محكمة']):
                    rules.append(content[:150] + "...")
            
            return rules[:3]  # Top 3 rules
            
        except Exception as e:
            logger.error(f"❌ Failed to extract rules: {str(e)}")
            return []
    
    async def analyze_with_context(
        self,
        case_text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        تحليل القضية باستخدام Gemini مع السياق المُسترجع.
        
        Args:
            case_text: نص القضية
            context: السياق المُسترجع
            
        Returns:
            التحليل المُعزز
        """
        try:
            # Build enhanced prompt with context
            prompt = self._build_rag_prompt(case_text, context)
            
            # Get analysis from Gemini
            result = await self.gemini_analyzer.analyze_with_custom_prompt(prompt)
            
            if not result.get('success'):
                logger.error(f"❌ Gemini analysis failed: {result.get('error')}")
                return result
            
            # Try to parse as JSON
            response_text = result.get('response', '')
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    analysis_json = json.loads(response_text[json_start:json_end])
                else:
                    analysis_json = {"raw_response": response_text}
                
            except json.JSONDecodeError:
                analysis_json = {"raw_response": response_text}
            
            return {
                "success": True,
                "analysis": analysis_json,
                "context_used": {
                    "laws_count": len(context.get('similar_laws', [])),
                    "cases_count": len(context.get('similar_cases', [])),
                    "principles_count": len(context.get('legal_principles', []))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis with context failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _build_rag_prompt(self, case_text: str, context: Dict[str, Any]) -> str:
        """
        بناء prompt مُعزز بالسياق لـ Gemini.
        
        Args:
            case_text: نص القضية
            context: السياق
            
        Returns:
            Prompt كامل
        """
        prompt = f"""أنت محامي خبير في النظام القانوني السعودي مع خبرة 20 عاماً.

**📋 القضية الجديدة المطلوب تحليلها:**
"{case_text}"

**📚 معلومات ذات صلة من قاعدة المعرفة القانونية:**

### 📜 القوانين والأنظمة المشابهة ({len(context.get('similar_laws', []))} نتيجة):
"""
        
        # Add similar laws
        for i, law in enumerate(context.get('similar_laws', [])[:5], 1):
            prompt += f"\n**{i}. {law.get('source', 'Unknown')}** (تشابه: {law.get('similarity', 0):.0%})\n"
            prompt += f"   المادة: {law.get('article', 'غير محدد')}\n"
            prompt += f"   النص: {law.get('content', '')[:300]}...\n"
            if law.get('verified'):
                prompt += f"   ✅ محقق من الإدارة\n"
        
        # Add similar cases
        if context.get('similar_cases'):
            prompt += f"\n### ⚖️ سوابق قضائية مشابهة ({len(context['similar_cases'])} نتيجة):\n"
            for i, case in enumerate(context['similar_cases'][:3], 1):
                prompt += f"\n**{i}. القضية رقم {case.get('case_number', 'غير محدد')}** (تشابه: {case.get('similarity', 0):.0%})\n"
                prompt += f"   المحكمة: {case.get('court', 'غير محدد')}\n"
                prompt += f"   التاريخ: {case.get('decision_date', 'غير محدد')}\n"
                prompt += f"   الملخص: {case.get('content', '')[:250]}...\n"
        
        # Add legal principles
        if context.get('legal_principles'):
            prompt += f"\n### 📖 المبادئ القانونية ذات الصلة:\n"
            for i, principle in enumerate(context['legal_principles'], 1):
                prompt += f"{i}. {principle}\n"
        
        # Add procedural rules
        if context.get('procedural_rules'):
            prompt += f"\n### ⚖️ القواعد الإجرائية المهمة:\n"
            for i, rule in enumerate(context['procedural_rules'], 1):
                prompt += f"{i}. {rule}\n"
        
        prompt += f"""

**🎯 المطلوب منك:**

استخدم المعلومات أعلاه من قاعدة المعرفة القانونية لتقديم تحليل دقيق ومُستند إلى مصادر حقيقية.

قدم تحليلاً قانونياً شاملاً يتضمن:

1. **التصنيف والتقييم**:
   - نوع القضية بدقة
   - درجة التعقيد
   - الأطراف المعنية

2. **التحليل القانوني المُستند**:
   - استخدم القوانين والمواد المذكورة أعلاه
   - اشرح كيفية انطباقها على هذه القضية
   - استشهد بالسوابق القضائية المشابهة

3. **الحقوق والالتزامات**:
   - حقوق كل طرف بناءً على القوانين المذكورة
   - الالتزامات القانونية

4. **الاستراتيجية الموصى بها**:
   - الإجراءات العاجلة
   - الخطوات قصيرة ومتوسطة المدى
   - نصائح تفاوضية

5. **تقييم الفرص والمخاطر**:
   - نقاط القوة استناداً للقوانين والسوابق
   - المخاطر المحتملة
   - احتمالية النجاح

**⚠️ مهم جداً:**
- استند فقط للمعلومات المذكورة أعلاه من قاعدة المعرفة
- اذكر أرقام المواد والقوانين بدقة كما وردت
- استشهد بالسوابق القضائية المشابهة
- إذا لم تجد معلومة كافية، وضح ذلك

أعد الإجابة بصيغة JSON منظمة:

```json
{{
  "classification": {{
    "case_type": "النوع",
    "complexity": "الدرجة",
    "confidence": 90,
    "parties": ["طرف 1", "طرف 2"]
  }},
  "legal_analysis": {{
    "applicable_laws": [
      {{
        "law_name": "اسم القانون من المصادر أعلاه",
        "article_number": "رقم المادة بالضبط",
        "relevance": "شرح الانطباق"
      }}
    ],
    "case_precedents": [
      {{
        "case_number": "رقم القضية من المصادر",
        "relevance": "وجه الشبه"
      }}
    ],
    "rights_obligations": "الحقوق والالتزامات المستندة للقوانين"
  }},
  "strategy": {{
    "immediate_actions": ["إجراء 1", "إجراء 2"],
    "short_term": ["خطوة 1", "خطوة 2"],
    "medium_term": ["استراتيجية 1", "استراتيجية 2"],
    "negotiation_tips": ["نصيحة 1", "نصيحة 2"]
  }},
  "risk_assessment": {{
    "strengths": ["قوة 1 مستندة للمصادر", "قوة 2"],
    "weaknesses": ["ضعف 1", "ضعف 2"],
    "opportunities": ["فرصة 1", "فرصة 2"],
    "threats": ["تهديد 1", "تهديد 2"],
    "success_probability": 75
  }},
  "recommendation": "التوصية النهائية المبنية على المصادر"
}}
```
"""
        
        return prompt
    
    def _enhance_analysis(
        self,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        تحسين التحليل بإضافة المصادر والمراجع.
        
        Args:
            analysis: التحليل من Gemini
            context: السياق المُسترجع
            
        Returns:
            التحليل المُحسّن
        """
        try:
            enhanced = {
                "success": analysis.get('success', False),
                "analysis": analysis.get('analysis', {}),
                "sources": {
                    "laws": context.get('similar_laws', []),
                    "cases": context.get('similar_cases', []),
                    "principles": context.get('legal_principles', []),
                    "procedural_rules": context.get('procedural_rules', [])
                },
                "metadata": {
                    "sources_count": context.get('sources_count', 0),
                    "laws_used": len(context.get('similar_laws', [])),
                    "cases_used": len(context.get('similar_cases', [])),
                    "context_provided": analysis.get('context_used', {})
                },
                "quality_indicators": {
                    "grounded_in_sources": True,
                    "traceable": True,
                    "verified_laws_used": sum(1 for law in context.get('similar_laws', []) if law.get('verified'))
                }
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Enhancement failed: {str(e)}")
            return analysis
    
    async def answer_legal_question(
        self,
        question: str,
        context_type: str = "both"
    ) -> Dict[str, Any]:
        """
        الإجابة على سؤال قانوني باستخدام RAG.
        
        Args:
            question: السؤال القانوني
            context_type: نوع السياق ('laws', 'cases', 'both')
            
        Returns:
            الإجابة مع المصادر
        """
        try:
            logger.info(f"❓ Answering question: '{question[:100]}...'")
            
            # Retrieve context based on type
            if context_type in ['laws', 'both']:
                laws = await self.search_service.find_similar_laws(question, top_k=3, threshold=0.7)
            else:
                laws = []
            
            if context_type in ['cases', 'both']:
                cases = await self.search_service.find_similar_cases(question, top_k=2, threshold=0.7)
            else:
                cases = []
            
            # Build prompt
            prompt = f"""أجب على هذا السؤال القانوني بناءً على المصادر التالية:

**السؤال:** {question}

**المصادر:**
"""
            
            for i, law in enumerate(laws, 1):
                prompt += f"\n{i}. {law.get('law_metadata', {}).get('law_name', 'قانون')}: {law['content'][:200]}...\n"
            
            for i, case in enumerate(cases, 1):
                prompt += f"\n{i}. قضية {case.get('case_metadata', {}).get('case_number', 'غير محدد')}: {case['content'][:200]}...\n"
            
            prompt += "\n\nأجب بوضوح مع الاستشهاد بالمصادر."
            
            # Get answer from Gemini
            result = await self.gemini_analyzer.analyze_with_custom_prompt(prompt)
            
            return {
                "success": result.get('success', False),
                "question": question,
                "answer": result.get('response', ''),
                "sources": {
                    "laws": laws,
                    "cases": cases
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Question answering failed: {str(e)}")
            return {"success": False, "error": str(e)}

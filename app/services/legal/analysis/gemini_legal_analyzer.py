"""
Gemini Legal Analyzer - محرك الذكاء الاصطناعي للتحليل القانوني

This service uses Google's Gemini AI to perform comprehensive legal analysis
for Arabic legal texts, specifically tailored for Saudi Arabian law.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiLegalAnalyzer:
    """
    محور الذكاء الاصطناعي في النظام - يستخدم Gemini لفهم وتحليل القانون.
    
    Features:
    - Comprehensive legal analysis using Gemini Pro
    - Arabic legal text understanding
    - Case classification and categorization
    - Legal strategy recommendations
    - Risk assessment
    - Procedural guidance
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Legal Analyzer.
        
        Args:
            api_key: Google AI API key (optional, defaults to env variable)
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ GOOGLE_AI_API_KEY not found. Gemini features will be disabled.")
            self.enabled = False
            return
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel('gemini-pro')
            
            # Generation config
            self.generation_config = {
                'temperature': 0.3,  # Lower for more focused legal analysis
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 4096,
            }
            
            # Safety settings (allow legal content)
            self.safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            self.enabled = True
            logger.info("✅ Gemini Legal Analyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.enabled = False
    
    def _create_comprehensive_prompt(self, case_text: str) -> str:
        """
        إنشاء prompt شامل للتحليل القانوني المتكامل.
        
        Args:
            case_text: نص القضية للتحليل
            
        Returns:
            Prompt منظم للتحليل
        """
        prompt = f"""أنت مستشار قانوني خبير في النظام القانوني السعودي، لديك خبرة 20 عاماً في المحاكم والقضايا القانونية.

**القضية المطلوب تحليلها:**
"{case_text}"

**المطلوب منك إعداد تحليل قانوني شامل ومحترف يتضمن:**

## 1️⃣ التصنيف الدقيق للقضية
- **النوع القانوني**: (مدني، جنائي، عمل، تجاري، إداري، أحوال شخصية، أو غيره)
- **الدرجة**: (بسيطة، متوسطة، معقدة)
- **درجة الثقة**: (نسبة مئوية من 0-100%)
- **الأطراف**: حدد الأطراف المعنية (مدعي، مدعى عليه، شهود، إلخ)

## 2️⃣ التحليل القانوني المفصل
- **الواقعة القانونية**: ما هي الوقائع الأساسية؟
- **الحقوق والالتزامات**: ما هي حقوق كل طرف وما هي التزاماته؟
- **الأدلة المتوفرة**: ما هي الأدلة الظاهرة في القضية؟
- **الإجراءات المطلوبة**: ما هي الخطوات القانونية الواجب اتخاذها؟

## 3️⃣ القوانين والأنظمة المنطبقة
- اذكر **القوانين والأنظمة السعودية** ذات العلاقة المباشرة
- اذكر **أرقام المواد** القانونية المحددة إن أمكن
- اشرح **كيفية الانطباق** على هذه القضية
- حدد **الشروط والأحكام** الواجب توافرها

## 4️⃣ تحليل الثغرات والفرص
- **ثغرات إجرائية**: هل هناك أخطاء أو نقاط ضعف إجرائية؟
- **نقاط ضعف الخصم**: ما هي نقاط الضعف في موقف الطرف الآخر؟
- **فرص للاستفادة**: ما هي الفرص القانونية التي يمكن استغلالها؟
- **مخاطر يجب تجنبها**: ما هي المخاطر القانونية التي يجب الحذر منها؟

## 5️⃣ الخطة الاستراتيجية والتوصيات
- **إجراءات عاجلة (24 ساعة)**: ماذا يجب فعله فوراً؟
- **إجراءات قصيرة المدى (أسبوع)**: ما هي الخطوات خلال الأسبوع القادم؟
- **إجراءات متوسطة المدى (شهر)**: ما هي الاستراتيجية الشهرية؟
- **نصائح تفاوضية**: كيف يمكن حل القضية ودياً؟

## 6️⃣ تقييم النتائج المحتملة
- **السيناريو الأفضل**: ما هو أفضل نتيجة ممكنة؟
- **السيناريو المتوقع**: ما هي النتيجة الأكثر احتمالاً؟
- **السيناريو الأسوأ**: ما هو أسوأ سيناريو محتمل؟
- **توصية نهائية**: ما هي التوصية العامة للتعامل مع القضية؟

**ملاحظات مهمة:**
- استخدم اللغة العربية الفصحى والمصطلحات القانونية الدقيقة
- كن محدداً وواضحاً في التوصيات
- اذكر أرقام المواد القانونية كلما أمكن
- قدم تحليلاً موضوعياً ومهنياً

**أعد الإجابة بصيغة JSON منظمة بهذا الشكل:**

```json
{{
  "classification": {{
    "case_type": "نوع القضية",
    "complexity": "الدرجة",
    "confidence": 85,
    "parties": ["المدعي", "المدعى عليه"]
  }},
  "legal_analysis": {{
    "facts": "الوقائع القانونية",
    "rights_obligations": "الحقوق والالتزامات",
    "evidence": ["دليل 1", "دليل 2"],
    "required_procedures": ["إجراء 1", "إجراء 2"]
  }},
  "applicable_laws": [
    {{
      "law_name": "اسم القانون",
      "article_numbers": ["المادة 1", "المادة 2"],
      "applicability": "شرح الانطباق",
      "conditions": "الشروط والأحكام"
    }}
  ],
  "gaps_opportunities": {{
    "procedural_gaps": ["ثغرة 1", "ثغرة 2"],
    "opponent_weaknesses": ["ضعف 1", "ضعف 2"],
    "opportunities": ["فرصة 1", "فرصة 2"],
    "risks": ["خطر 1", "خطر 2"]
  }},
  "strategic_plan": {{
    "urgent_24h": ["إجراء 1", "إجراء 2"],
    "short_term_week": ["خطوة 1", "خطوة 2"],
    "medium_term_month": ["استراتيجية 1", "استراتيجية 2"],
    "negotiation_tips": ["نصيحة 1", "نصيحة 2"]
  }},
  "outcome_assessment": {{
    "best_case": "أفضل نتيجة",
    "expected_case": "النتيجة المتوقعة",
    "worst_case": "أسوأ نتيجة",
    "recommendation": "التوصية النهائية"
  }}
}}
```
"""
        return prompt
    
    async def comprehensive_legal_analysis(self, case_text: str) -> Dict[str, Any]:
        """
        يقوم بتحليل قانوني شامل للقضية المُدخلة.
        
        Args:
            case_text: نص القضية للتحليل
            
        Returns:
            تحليل قانوني شامل بصيغة dict
        """
        if not self.enabled:
            logger.error("❌ Gemini is not enabled. Cannot perform analysis.")
            return {
                "success": False,
                "error": "Gemini AI is not configured. Please set GOOGLE_AI_API_KEY.",
                "analysis": None
            }
        
        try:
            logger.info(f"🔍 Starting comprehensive legal analysis for case: '{case_text[:100]}...'")
            
            # Create prompt
            prompt = self._create_comprehensive_prompt(case_text)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Extract text
            analysis_text = response.text
            
            # Try to parse JSON from response
            try:
                # Find JSON in response
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_text[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    # If no JSON found, create structured response from text
                    analysis_data = {
                        "raw_analysis": analysis_text,
                        "parsed": False
                    }
                    logger.warning("⚠️ Could not parse JSON from Gemini response")
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parsing failed: {str(e)}")
                analysis_data = {
                    "raw_analysis": analysis_text,
                    "parsed": False
                }
            
            # Add metadata
            result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "case_text": case_text,
                "analysis": analysis_data,
                "model": "gemini-pro",
                "tokens_used": len(case_text.split()) + len(analysis_text.split())
            }
            
            logger.info(f"✅ Analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze case with Gemini: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    async def quick_case_classification(self, case_text: str) -> Dict[str, Any]:
        """
        تصنيف سريع للقضية (أخف وأسرع من التحليل الشامل).
        
        Args:
            case_text: نص القضية
            
        Returns:
            تصنيف القضية
        """
        if not self.enabled:
            return {"success": False, "error": "Gemini not enabled"}
        
        try:
            prompt = f"""أنت خبير قانوني. صنف هذه القضية بإيجاز:

"{case_text}"

أعد JSON فقط:
{{
  "case_type": "النوع (مدني/جنائي/عمل/تجاري/إداري)",
  "complexity": "الدرجة (بسيطة/متوسطة/معقدة)",
  "confidence": 85,
  "key_issue": "القضية الرئيسية في جملة واحدة"
}}"""
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON
            text = response.text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                classification = json.loads(text[json_start:json_end])
                return {"success": True, "classification": classification}
            
            return {"success": False, "error": "Could not parse classification"}
            
        except Exception as e:
            logger.error(f"❌ Classification failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_legal_entities(self, case_text: str) -> Dict[str, Any]:
        """
        استخراج الكيانات القانونية من النص (أسماء، تواريخ، مبالغ، إلخ).
        
        Args:
            case_text: نص القضية
            
        Returns:
            الكيانات المستخرجة
        """
        if not self.enabled:
            return {"success": False, "error": "Gemini not enabled"}
        
        try:
            prompt = f"""استخرج الكيانات القانونية من هذا النص:

"{case_text}"

أعد JSON فقط:
{{
  "parties": ["اسم 1", "اسم 2"],
  "dates": ["تاريخ 1", "تاريخ 2"],
  "amounts": ["مبلغ 1", "مبلغ 2"],
  "locations": ["مكان 1", "مكان 2"],
  "documents": ["مستند 1", "مستند 2"],
  "laws_mentioned": ["قانون 1", "قانون 2"]
}}"""
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                entities = json.loads(text[json_start:json_end])
                return {"success": True, "entities": entities}
            
            return {"success": False, "error": "Could not parse entities"}
            
        except Exception as e:
            logger.error(f"❌ Entity extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_legal_strategy(self, case_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        توليد استراتيجية قانونية مفصلة بناءً على التحليل.
        
        Args:
            case_analysis: التحليل السابق للقضية
            
        Returns:
            استراتيجية قانونية
        """
        if not self.enabled:
            return {"success": False, "error": "Gemini not enabled"}
        
        try:
            prompt = f"""بناءً على هذا التحليل القانوني:

{json.dumps(case_analysis, ensure_ascii=False, indent=2)}

أعد استراتيجية قانونية تفصيلية كـ JSON:
{{
  "immediate_actions": ["فعل 1", "فعل 2", "فعل 3"],
  "documents_needed": ["مستند 1", "مستند 2"],
  "witnesses_to_contact": ["شاهد 1", "شاهد 2"],
  "legal_arguments": ["حجة 1", "حجة 2"],
  "negotiation_strategy": "الاستراتيجية التفاوضية",
  "litigation_strategy": "استراتيجية الترافع",
  "settlement_options": ["خيار 1", "خيار 2"],
  "estimated_timeline": "الجدول الزمني المتوقع",
  "estimated_costs": "التكاليف المتوقعة",
  "success_probability": 75
}}"""
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                strategy = json.loads(text[json_start:json_end])
                return {"success": True, "strategy": strategy}
            
            return {"success": False, "error": "Could not parse strategy"}
            
        except Exception as e:
            logger.error(f"❌ Strategy generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def analyze_with_custom_prompt(self, custom_prompt: str) -> Dict[str, Any]:
        """
        تحليل مخصص باستخدام prompt من المستخدم.
        
        Args:
            custom_prompt: Prompt مخصص
            
        Returns:
            نتيجة التحليل
        """
        if not self.enabled:
            return {"success": False, "error": "Gemini not enabled"}
        
        try:
            response = self.model.generate_content(
                custom_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            return {
                "success": True,
                "response": response.text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Custom analysis failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def is_enabled(self) -> bool:
        """التحقق من أن Gemini مفعّل ويعمل."""
        return self.enabled

"""
Gemini-based parser implementing a small interface that returns hierarchy.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GeminiParser:
    """Thin wrapper around Gemini to extract hierarchy JSON."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    async def parse(self, file_path: str, law_source_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            if not self._client:
                try:
                    from google import genai  # type: ignore
                    self._client = genai.Client(api_key=self.api_key)
                except Exception as e:
                    return {"success": False, "message": f"Gemini SDK not available: {e}", "data": None}

            file_ext = os.path.splitext(file_path)[1].lower()
            mime = {
                ".pdf": "application/pdf",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }.get(file_ext)
            if not mime:
                return {"success": False, "message": f"Unsupported file type: {file_ext}", "data": None}

            with open(file_path, "rb") as f:
                content = f.read()

            # Check file size to prevent timeouts
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > 20:  # Limit to 20MB
                return {"success": False, "message": f"File too large ({file_size_mb:.1f}MB). Maximum size is 20MB.", "data": None}

            try:
                from google.genai import types  # type: ignore
            except Exception as e:
                return {"success": False, "message": f"Gemini SDK not available: {e}", "data": None}

            part = types.Part.from_bytes(data=content, mime_type=mime)
            name = (law_source_details or {}).get("name") or "القانون"
            prompt = self._prompt(name)
            
            logger.info(f"Starting Gemini AI processing for: {name}")
            logger.info(f"File size: {len(content)} bytes, MIME type: {mime}")
            
            # Add timeout protection for Gemini API call
            try:
                resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.models.generate_content,
                        model="gemini-2.5-flash",
                        contents=[part, prompt]
                    ),
                    timeout=300  # 5 minutes timeout
                )
                logger.info("Gemini AI processing completed successfully")
                text = getattr(resp, "text", "")
            except asyncio.TimeoutError:
                logger.error("Gemini AI processing timed out after 5 minutes")
                return {"success": False, "message": "Gemini AI processing timed out after 5 minutes", "data": None}
            except Exception as e:
                logger.error(f"Gemini AI API call failed: {e}")
                return {"success": False, "message": f"Gemini AI API call failed: {e}", "data": None}
            data = self._parse_json(text)
            if not data:
                return {"success": False, "message": "AI response not parseable as JSON", "data": None}
            
            # Handle the comprehensive structure from the working script
            if "law_sources" in data and data["law_sources"]:
                # Extract the first law source and its branches
                law_source = data["law_sources"][0]
                branches = law_source.get("branches", [])
                
                # Log processing report if available
                processing_report = data.get("processing_report", {})
                logger.info(f"Processing report: {processing_report}")
                
                return {
                    "success": True, 
                    "message": f"AI parsed successfully. Extracted {len(branches)} branches, {processing_report.get('total_articles', 0)} articles", 
                    "data": {
                        "hierarchy": {"branches": branches},
                        "law_source": law_source,
                        "processing_report": processing_report
                    }
                }
            elif "branches" in data:
                # Fallback for simpler structure
                return {"success": True, "message": "AI parsed", "data": {"hierarchy": {"branches": data.get("branches", [])}}}
            else:
                return {"success": False, "message": "No valid law structure found in AI response", "data": None}
        except Exception as e:
            logger.error(f"Gemini parse failed: {e}")
            return {"success": False, "message": f"Gemini parse failed: {e}", "data": None}

    def _prompt(self, law_name: str) -> str:
        return f"""
أنت خبير في تحليل الوثائق القانونية العربية. مهمتك هي استخراج النص القانوني وتنظيمه في هيكل JSON منظم وفقاً للنماذج التالية:

## الهيكل المطلوب:

### 1. LawSource (المصدر القانوني)
- name: اسم القانون أو التشريع
- type: نوع المصدر (law, regulation, code, directive, decree)
- jurisdiction: الاختصاص القضائي أو الدولة
- issuing_authority: السلطة المصدرة
- issue_date: تاريخ الإصدار
- description: وصف مختصر للمصدر
- status: حالة المعالجة (raw, processed, indexed)

### 2. LawBranch (الأبواب القانونية)
- branch_number: رقم الباب
- branch_name: اسم الباب
- description: وصف الباب
- order_index: ترتيب الباب

### 3. LawChapter (الفصول القانونية)
- chapter_number: رقم الفصل
- chapter_name: اسم الفصل
- description: وصف الفصل
- order_index: ترتيب الفصل

### 4. LawArticle (المواد القانونية)
- article_number: رقم المادة
- title: عنوان المادة (إن وجد)
- content: نص المادة الكامل
- keywords: الكلمات المفتاحية المستخرجة
- order_index: ترتيب المادة داخل الفصل

## التعليمات:

1. **تحليل النص**: اقرأ النص بعناية وحدد نوع الوثيقة (قانون، قضية، لائحة، إلخ)

2. **استخراج الهيكل الهرمي**: 
   - حدد الأبواب (Branches) إذا كانت موجودة
   - حدد الفصول (Chapters) داخل كل باب
   - استخرج المواد (Articles) مع أرقامها ونصوصها

3. **الكلمات المفتاحية**: استخرج الكلمات المفتاحية القانونية المهمة من كل مادة

4. **الترقيم**: احافظ على ترتيب المواد والفصول والأبواب كما هو في النص الأصلي

## مثال على JSON المطلوب:

```json
{{
  "law_sources": [
    {{
      "name": "قانون الجزاء الميرامي",
      "type": "law",
      "jurisdiction": "ميرام",
      "issuing_authority": "السلطة التشريعية",
      "description": "القانون الأساسي للعقوبات في دولة ميرام",
      "status": "raw",
      "branches": [
        {{
          "branch_number": "1",
          "branch_name": "أحكام عامة",
          "description": "الأحكام العامة للجريمة والعقوبة",
          "order_index": 1,
          "chapters": [
            {{
              "chapter_number": "1",
              "chapter_name": "تعريف الجريمة والفاعل",
              "description": "تعريفات أساسية للجريمة والفاعل",
              "order_index": 1,
              "articles": [
                {{
                  "article_number": "20",
                  "title": "تعريف الفاعل",
                  "content": "يعد فاعلاً للجريمة كل من أبرز إلى حيز الوجود أحد العناصر التي تؤلف الجريمة أو ساهم مباشرة في تنفيذها أو حرض عليها.",
                  "keywords": ["فاعل", "جريمة", "عناصر", "تحريض"],
                  "order_index": 1
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "processing_report": {{
    "warnings": [],
    "errors": [],
    "suggestions": ["تحقق من ترقيم المواد", "تأكد من اكتمال النصوص"],
    "structure_confidence": 0.95,
    "total_chapters": 5,
    "total_articles": 25,
    "total_cases": 0
  }}
}}
```

## ملاحظات مهمة:

1. **الدقة**: تأكد من استخراج النصوص بدقة تامة دون إضافة أو حذف
2. **الترقيم**: احافظ على أرقام المواد والفصول كما هي
3. **التصنيف**: صنف كل جزء بشكل صحيح (قانون، قضية، مادة، إلخ)
4. **الكلمات المفتاحية**: استخرج الكلمات المهمة قانونياً
5. **الهيكل**: احافظ على التسلسل الهرمي للوثيقة

الآن، قم بتحليل النص المرفق واستخراجه في الهيكل JSON المطلوب أعلاه.

اسم القانون: {law_name}. لا تضع شروحات أو أسوار كود.
"""

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            pass
        try:
            import re
            m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
            if m:
                return json.loads(m.group(1))
        except Exception:
            pass
        try:
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1 and e > s:
                return json.loads(text[s:e+1])
        except Exception:
            pass
        return None



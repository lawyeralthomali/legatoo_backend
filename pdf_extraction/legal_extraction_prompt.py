"""
Legal Document Extraction Prompt for Gemini API
This script contains a comprehensive prompt to extract legal documents into structured JSON format
based on the legal knowledge management system models.
"""

def get_legal_extraction_prompt():
    """
    Returns a comprehensive prompt for extracting legal documents into structured JSON format.
    This prompt is designed to work with Arabic legal documents and extract them according to
    the legal knowledge management system's hierarchical structure.
    """
    
    prompt = """
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

### 5. LegalCase (القضايا القانونية)
- case_number: رقم القضية
- title: عنوان القضية
- description: وصف القضية
- jurisdiction: الاختصاص القضائي
- court_name: اسم المحكمة
- decision_date: تاريخ القرار
- case_type: نوع القضية (مدني، جنائي، تجاري، عمل، إداري)
- court_level: درجة المحكمة (ابتدائي، استئناف، تمييز، عالي)

### 6. CaseSection (أقسام القضية)
- section_type: نوع القسم (summary, facts, arguments, ruling, legal_basis)
- content: محتوى القسم

## التعليمات:

1. **تحليل النص**: اقرأ النص بعناية وحدد نوع الوثيقة (قانون، قضية، لائحة، إلخ)

2. **استخراج الهيكل الهرمي**: 
   - حدد الأبواب (Branches) إذا كانت موجودة
   - حدد الفصول (Chapters) داخل كل باب
   - استخرج المواد (Articles) مع أرقامها ونصوصها

3. **للقضايا القانونية**:
   - استخرج تفاصيل القضية من النص
   - قسم المحتوى إلى أقسام منطقية (الوقائع، الحجج، الحكم، الأساس القانوني)

4. **الكلمات المفتاحية**: استخرج الكلمات المفتاحية القانونية المهمة من كل مادة

5. **الترقيم**: احافظ على ترتيب المواد والفصول والأبواب كما هو في النص الأصلي

## مثال على JSON المطلوب:

```json
{
  "law_sources": [
    {
      "name": "قانون الجزاء الميرامي",
      "type": "law",
      "jurisdiction": "ميرام",
      "issuing_authority": "السلطة التشريعية",
      "description": "القانون الأساسي للعقوبات في دولة ميرام",
      "status": "raw",
      "branches": [
        {
          "branch_number": "1",
          "branch_name": "أحكام عامة",
          "description": "الأحكام العامة للجريمة والعقوبة",
          "order_index": 1,
          "chapters": [
            {
              "chapter_number": "1",
              "chapter_name": "تعريف الجريمة والفاعل",
              "description": "تعريفات أساسية للجريمة والفاعل",
              "order_index": 1,
              "articles": [
                {
                  "article_number": "20",
                  "title": "تعريف الفاعل",
                  "content": "يعد فاعلاً للجريمة كل من أبرز إلى حيز الوجود أحد العناصر التي تؤلف الجريمة أو ساهم مباشرة في تنفيذها أو حرض عليها.",
                  "keywords": ["فاعل", "جريمة", "عناصر", "تحريض"],
                  "order_index": 1
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "legal_cases": [
    {
      "case_number": "قضية أفنان",
      "title": "قضية تزوير العملة والاتجار بالبشر",
      "description": "قضية تتعلق بتزوير العملة والاتجار بالبشر في منتجع أفنان",
      "jurisdiction": "ميرام",
      "court_name": "محكمة الجنايات",
      "case_type": "جنائي",
      "court_level": "جنايات",
      "sections": [
        {
          "section_type": "facts",
          "content": "يقع المنتجع السياحي الساحلي (أفنان) في مدينة (سقاف)..."
        },
        {
          "section_type": "legal_basis",
          "content": "التهم الموجهة: التزوير، الاتجار بالبشر، الاتجار بالمخدرات، غسل الأموال"
        }
      ]
    }
  ],
  "processing_report": {
    "warnings": [],
    "errors": [],
    "suggestions": ["تحقق من ترقيم المواد", "تأكد من اكتمال النصوص"],
    "structure_confidence": 0.95,
    "total_chapters": 5,
    "total_articles": 25,
    "total_cases": 1
  }
}
```

## ملاحظات مهمة:

1. **الدقة**: تأكد من استخراج النصوص بدقة تامة دون إضافة أو حذف
2. **الترقيم**: احافظ على أرقام المواد والفصول كما هي
3. **التصنيف**: صنف كل جزء بشكل صحيح (قانون، قضية، مادة، إلخ)
4. **الكلمات المفتاحية**: استخرج الكلمات المهمة قانونياً
5. **الهيكل**: احافظ على التسلسل الهرمي للوثيقة

الآن، قم بتحليل النص المرفق واستخراجه في الهيكل JSON المطلوب أعلاه.
"""

    return prompt

def get_simple_extraction_prompt():
    """
    Returns a simplified prompt for basic legal text extraction.
    """
    
    prompt = """
استخرج النص القانوني التالي في هيكل JSON منظم:

1. حدد نوع الوثيقة (قانون، قضية، لائحة)
2. استخرج المواد القانونية مع أرقامها ونصوصها
3. إذا كانت قضية، استخرج تفاصيل القضية
4. استخرج الكلمات المفتاحية المهمة

```json
{
  "document_type": "law|case|regulation",
  "title": "عنوان الوثيقة",
  "articles": [
    {
      "number": "رقم المادة",
      "content": "نص المادة"
    }
  ],
  "keywords": ["كلمة1", "كلمة2"],
  "summary": "ملخص مختصر"
}
```

النص المراد تحليله:
"""

    return prompt

if __name__ == "__main__":
    # Example usage
    print("Legal Extraction Prompt:")
    print("=" * 50)
    print(get_legal_extraction_prompt())

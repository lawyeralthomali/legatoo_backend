from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv("../supabase.env")

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_KEY)
# 1. إعداد العميل (كما كان سابقاً)
client = genai.Client(api_key=GEMINI_KEY) 

pdf_file_path = "test3.pdf" # **المسار إلى ملف PDF**
output_text_file = "extracted_legal_structure.json" # **اسم الملف JSON الناتج**

prompt_text = """
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

# 2. استخراج النص باستخدام Gemini API

# قراءة محتويات ملف PDF كـ بايت
with open(pdf_file_path, "rb") as f:
    pdf_bytes = f.read()

# إنشاء الجزء الخاص بملف PDF
pdf_part = types.Part.from_bytes(
    data=pdf_bytes,
    mime_type='application/pdf'
)

# إرسال الطلب
print("جاري إرسال الطلب إلى Gemini API...")
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[pdf_part, prompt_text]
)

# الحصول على النص المستخرج
extracted_text = response.text
print("تم استخراج النص بنجاح.")

# 3. تخزين النص المستخرج في ملف نصي
try:
    with open(output_text_file, 'w', encoding='utf-8') as f:
        f.write(extracted_text)
    
    print(f"\nتم حفظ النص المستخرج بنجاح في الملف: {output_text_file}")
    
except Exception as e:
    print(f"\nحدث خطأ أثناء حفظ الملف: {e}")
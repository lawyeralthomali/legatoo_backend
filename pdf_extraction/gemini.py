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
output_text_file = "extracted_content.txt" # **اسم الملف النصي الناتج**

prompt_text = "استخرج النص الكامل والمُنظم من ملف PDF هذا. حافظ على تنسيق الفقرات والعناوين الرئيسية."

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
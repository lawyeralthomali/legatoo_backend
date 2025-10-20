import os, tempfile, json, re
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from google import genai

# ---------------------------------
# إعداد النماذج والمجلدات
# ---------------------------------
VECTORSTORE_PATH = "./vector_store"
os.makedirs(VECTORSTORE_PATH, exist_ok=True)

EMBEDDING_MODEL = "Omartificial-Intelligence-Space/GATE-AraBert-v1"
RERANKER_MODEL = "Omartificial-Intelligence-Space/ARA-Reranker-V1"

# Load Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=GEMINI_API_KEY)

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
reranker_model = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL)
compressor = CrossEncoderReranker(model=reranker_model, top_n=5)

# ---------------------------------
# رفع الملف ومعالجته
# ---------------------------------
async def process_upload(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    with open(tmp_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # تنظيف الملف المؤقت
    os.unlink(tmp_path)

    # ✅ التحقق من الهيكل الجديد للملف
    if "law_sources" not in data:
        raise ValueError("❌ هيكل الملف غير صحيح - المفتاح 'law_sources' مفقود")

    law_source = data["law_sources"]
    
    # ✅ التحقق من وجود المفاتيح الأساسية
    if "articles" not in law_source:
        raise ValueError("❌ المفتاح 'articles' مفقود في البيانات")

    # ✅ تحويل المقالات إلى مستندات مع معلومات إضافية
    documents = []
    for article in law_source["articles"]:
        # التحقق من وجود البيانات الأساسية
        if not article.get("text") or not article.get("article"):
            continue  # تخطي المقالات الفارغة
            
        # إنشاء مستند مع معلومات كاملة
        document = Document(
            page_content=article["text"],
            metadata={
                "article": article["article"],
                "keywords": article.get("keywords", []),
                "order_index": article.get("order_index", 0),
                "law_name": law_source.get("name", ""),
                "law_type": law_source.get("type", ""),
                "jurisdiction": law_source.get("jurisdiction", ""),
                "issuing_authority": law_source.get("issuing_authority", ""),
                "issue_date": law_source.get("issue_date", "")
            }
        )
        documents.append(document)

    if not documents:
        raise ValueError("❌ لم يتم العثور على مقالات صالحة في الملف")

    # تقسيم النصوص إلى chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # إنشاء أو تحديث التضمينات
    if os.path.exists(f"{VECTORSTORE_PATH}/index.faiss"):
        # إذا كان هناك تخزين موجود، نحدثه
        existing_vectorstore = FAISS.load_local(
            VECTORSTORE_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        existing_vectorstore.add_documents(chunks)
        existing_vectorstore.save_local(VECTORSTORE_PATH)
        chunks_count = len(chunks)
    else:
        # إذا لم يكن موجود، ننشئ جديد
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(VECTORSTORE_PATH)
        chunks_count = len(chunks)

    return chunks_count

async def answer_query(query: str):
    if not os.path.exists(f"{VECTORSTORE_PATH}/index.faiss"):
        return "❌ لم يتم رفع الملفات أو إنشاء قاعدة التضمينات بعد."

    # تحميل قاعدة التضمينات
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)

    # البحث الدلالي
    base_docs = vectorstore.similarity_search(query, k=20)
    
    # إعادة ترتيب النتائج
    reranked_docs = compressor.compress_documents(base_docs, query)

    # ✅ بناء السياق مع معلومات إضافية (تم تغيير طريقة بناء السياق لزيادة التركيز)
    context_parts = []
    
    # تخزين السياق المسترجع في قائمة منفصلة ليتم إرجاعها
    retrieved_context = [] 
    
    for doc in reranked_docs:
        metadata = doc.metadata
        
        # جزء السياق للاستخدام الداخلي (للتوليد)
        context_part_for_generation = f"""
== **{metadata.get('law_name', '')}** ==
**المادة:** {metadata.get('article', 'غير محدد')}
**النص:** {doc.page_content}
(المرجع: {metadata.get('issuing_authority', '')} - {metadata.get('issue_date', '')})
        """
        context_parts.append(context_part_for_generation.strip())
        
        # جزء السياق للإرجاع للمستخدم (لتسهيل القراءة)
        retrieved_context.append({
            "article": metadata.get('article', 'غير محدد'),
            "law_name": metadata.get('law_name', ''),
            "text": doc.page_content,
            "source": f"{metadata.get('issuing_authority', '')} - {metadata.get('issue_date', '')}"
        })

    context_text = "\n\n" + "="*50 + "\n\n".join(context_parts) + "\n" + "="*50

    # ✅ تصحيح الـ Prompt ليتوافق مع أي قانون يتم رفعه
    prompt = f"""
أنت مساعد قانوني سعودي متخصص في النظام القانوني المتعلق بالسياق المقدم لك.

**التعليمات:**
1. استخرج الإجابة من النصوص القانونية المقدمة **فقط** ولا تجب من معلوماتك العامة.
2. اذكر رقم المادة والنص القانوني بدقة.
3. أجب باللغة العربية الفصحى.
4. كن دقيقاً وواضحاً في الإجابة.

**النصوص القانونية المرجعية:**
{context_text}

**السؤال:**
{query}

**ملاحظة:** إذا لم تجد الإجابة في النصوص أعلاه، قل: "لم أجد نصاً قانونياً يغطي هذا السؤال بشكل محدد"
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.1,  # أقل لزيادة الدقة
                "max_output_tokens": 2000,
                "top_p": 0.8
            }
        )
        
        # التأكد من وجود استجابة صحيحة
        if response and hasattr(response, 'text') and response.text:
            return {
                "answer": response.text, 
                "retrieved_context": retrieved_context # إرجاع السياق المسترجع
            }
        else:
            return {
                "answer": "❌ لم يتم الحصول على إجابة مناسبة من النموذج.",
                "retrieved_context": retrieved_context
            }
            
    except Exception as e:
        return {
            "answer": f"⚠️ حدث خطأ أثناء الاتصال بـ Gemini: {e}",
            "retrieved_context": retrieved_context
        }
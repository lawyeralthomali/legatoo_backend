import os, tempfile, json, re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from google import genai
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_community.vectorstores.utils import filter_complex_metadata

from ...db.database import AsyncSessionLocal
from ..query_log_service import QueryLogService

# ---------------------------------
# إعداد النماذج والمجلدات
# ---------------------------------
VECTORSTORE_PATH = "./chroma_store"
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

    # تقسيم النصوص إلى chunks بدون الاعتماد على كائنات Document
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    texts: list[str] = []
    metadatas: list[dict] = []
    for base_doc in documents:
        base_text = base_doc.page_content if isinstance(base_doc, Document) else str(base_doc)
        raw_md = base_doc.metadata if isinstance(base_doc, Document) and isinstance(base_doc.metadata, dict) else {}
        # تصفية/تسطيح الميتاداتا لتتوافق مع Chroma (سلاسل/أرقام/منطقي فقط)
        base_md: dict = {}
        for key, value in raw_md.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                base_md[key] = value
            elif isinstance(value, list):
                try:
                    base_md[key] = ", ".join(map(str, value))
                except Exception:
                    base_md[key] = str(value)
            else:
                base_md[key] = str(value)
        # تقسيم النص وإضافة كل جزء مع نفس الميتاداتا الأساسية
        parts = splitter.split_text(base_text)
        for part in parts:
            texts.append(part)
            metadatas.append(dict(base_md))

    # إنشاء أو تحديث التضمينات باستخدام Chroma مع مجلد دائم
    # Chroma يقوم بالحفظ تلقائياً في مجلد persistance
    vectorstore = Chroma(
        collection_name="legal_knowledge",
        embedding_function=embeddings,
        persist_directory=VECTORSTORE_PATH,
    )
    # إذا كان هناك مستندات جديدة، أضفها إلى المجموعة الحالية
    if texts:
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        # persist للتأكد من التخزين
        vectorstore.persist()
    chunks_count = len(texts)

    return chunks_count

async def answer_query(query: str, user_id: int | None = None):
    # تهيئة متجر Chroma الدائم
    vectorstore = Chroma(
        collection_name="legal_knowledge",
        embedding_function=embeddings,
        persist_directory=VECTORSTORE_PATH,
    )
    # التحقق من وجود أي بيانات قبل البحث
    # Chroma لا يوفر فحص ملف مثل FAISS، سنحاول البحث وإن لم توجد بيانات سيعيد نتيجة فارغة

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
            result_payload = {
                "answer": response.text, 
                "retrieved_context": retrieved_context # إرجاع السياق المسترجع
            }
        else:
            result_payload = {
                "answer": "❌ لم يتم الحصول على إجابة مناسبة من النموذج.",
                "retrieved_context": retrieved_context
            }
        # Log query and answer asynchronously using a DB session
        async with AsyncSessionLocal() as db:
            service = QueryLogService(db)
            await service.log_query_answer(
                user_id=user_id,
                query=query,
                retrieved_articles=retrieved_context,
                generated_answer=result_payload.get("answer"),
            )
        return result_payload
            
    except Exception as e:
        error_payload = {
            "answer": f"⚠️ حدث خطأ أثناء الاتصال بـ Gemini: {e}",
            "retrieved_context": retrieved_context
        }
        # Best-effort logging even on errors
        try:
            async with AsyncSessionLocal() as db:
                service = QueryLogService(db)
                await service.log_query_answer(
                    user_id=user_id,
                    query=query,
                    retrieved_articles=retrieved_context,
                    generated_answer=error_payload.get("answer"),
                )
        except Exception:
            pass
        return error_payload
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

client = genai.Client(api_key="AIzaSyDrNGFCsJvs2ek3ug0DpUyoL2j1oZSHD0Y")

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

    # تحويل JSON إلى مستندات
    documents = [
        Document(page_content=item.get("text", ""), metadata={"article": item.get("article", "")})
        for item in data
    ]

    # تقسيم النصوص إلى chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # إنشاء التضمينات وحفظها في FAISS
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(VECTORSTORE_PATH)

    return len(chunks)

# ---------------------------------
# معالجة الاستفسار / السؤال
# ---------------------------------
async def answer_query(query: str):
    if not os.path.exists(f"{VECTORSTORE_PATH}/index.faiss"):
        return "❌ لم يتم رفع الملفات أو إنشاء قاعدة التضمينات بعد."

    # تحميل قاعدة التضمينات
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)

    # البحث الدلالي
    base_docs = vectorstore.similarity_search(query, k=20)
    reranked_docs = compressor.compress_documents(base_docs, query)

    # تحويل النصوص إلى سياق واحد
    context_text = "\n\n".join([f"{d.metadata.get('article','')}:\n{d.page_content}" for d in reranked_docs])

    prompt = f"""
أنت مساعد قانوني سعودي مختص في نظام العمل.
استخرج الجواب من النصوص التالية فقط واذكر رقم المادة المرجعية بوضوح.

النصوص القانونية:
{context_text}

السؤال: {query}

أجب بالعربية الرسمية بدقة وإيجاز.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0, "max_output_tokens": 1500}
        )
        return response.text
    except Exception as e:
        return f"⚠️ حدث خطأ أثناء الاتصال بـ Gemini: {e}"

"""
متطلبات النظام الجديد مع دعم قاعدة البيانات المزدوجة
"""

# الحزم المطلوبة
REQUIRED_PACKAGES = [
    "sqlalchemy>=2.0.0",
    "chromadb>=0.4.0", 
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "langchain-huggingface>=0.0.1",
    "langchain-core>=0.1.0",
    "asyncio",
    "fastapi>=0.100.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.6",
    "aiofiles>=23.0.0",
    "ijson>=3.2.0"
]

# متغيرات البيئة المطلوبة
REQUIRED_ENV_VARS = [
    "GEMINI_API_KEY",  # مفتاح API لـ Gemini
    "DATABASE_URL",    # رابط قاعدة البيانات SQL
]

# إعدادات النظام
SYSTEM_CONFIG = {
    "vectorstore_path": "./chroma_store",
    "embedding_model": "Omartificial-Intelligence-Space/GATE-AraBert-v1",
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "batch_size": 50,
    "collection_name": "legal_knowledge"
}

# اختبار التثبيت
def test_installation():
    """اختبار تثبيت جميع الحزم المطلوبة"""
    import importlib
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        package_name = package.split(">=")[0].split("==")[0]
        try:
            importlib.import_module(package_name.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ الحزم التالية مفقودة:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nلتثبيت الحزم المفقودة:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ جميع الحزم المطلوبة مثبتة")
        return True

# اختبار متغيرات البيئة
def test_environment():
    """اختبار متغيرات البيئة المطلوبة"""
    import os
    missing_vars = []
    
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ متغيرات البيئة التالية مفقودة:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("✅ جميع متغيرات البيئة موجودة")
        return True

if __name__ == "__main__":
    print("🔍 فحص متطلبات النظام الجديد...\n")
    
    packages_ok = test_installation()
    env_ok = test_environment()
    
    if packages_ok and env_ok:
        print("\n🎉 النظام جاهز للعمل!")
    else:
        print("\n⚠️ يرجى إصلاح المشاكل أعلاه قبل تشغيل النظام")

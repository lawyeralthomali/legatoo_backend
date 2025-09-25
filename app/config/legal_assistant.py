"""
Legal Assistant Configuration
Converted from Django settings and views
"""
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class LegalAssistantConfig(BaseModel):
    """Configuration for Legal Assistant service"""
    
    # API Keys
    openai_api_key: str = Field(default="")
    google_api_key: str = Field(default="")
    
    # Model Configuration
    default_model: str = Field(default="gpt-4")
    fallback_model: str = Field(default="gpt-3.5-turbo")
    embedding_model: str = Field(default="text-embedding-3-small")
    
    # Token Configuration
    max_tokens: int = Field(default=1500)
    max_context_tokens: int = Field(default=8000)
    max_fallback_tokens: int = Field(default=1000)
    
    # Temperature and AI Parameters
    temperature: float = Field(default=0.3)
    top_p: float = Field(default=0.9)
    frequency_penalty: float = Field(default=0.1)
    presence_penalty: float = Field(default=0.1)
    
    # Search Configuration
    top_k: int = Field(default=5)
    max_sources: int = Field(default=3)
    
    # Language Detection
    arabic_threshold: float = Field(default=0.3)
    
    # File Upload Configuration
    max_file_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: List[str] = Field(default=[".pdf", ".doc", ".docx", ".txt"])
    
    # Media Configuration
    media_url: str = Field(default="/media/")
    media_root: str = Field(default="media")
    
    # Session Configuration
    session_cookie_age: int = Field(default=3600)  # 1 hour
    
    # Quality Assessment
    high_quality_threshold: int = Field(default=200)
    
    @classmethod
    def from_env(cls) -> "LegalAssistantConfig":
        """Create configuration from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            default_model=os.getenv("LEGAL_ASSISTANT_DEFAULT_MODEL", "gpt-4"),
            fallback_model=os.getenv("LEGAL_ASSISTANT_FALLBACK_MODEL", "gpt-3.5-turbo"),
            embedding_model=os.getenv("LEGAL_ASSISTANT_EMBEDDING_MODEL", "text-embedding-3-small"),
            max_tokens=int(os.getenv("LEGAL_ASSISTANT_MAX_TOKENS", "1500")),
            max_context_tokens=int(os.getenv("LEGAL_ASSISTANT_MAX_CONTEXT_TOKENS", "8000")),
            max_fallback_tokens=int(os.getenv("LEGAL_ASSISTANT_MAX_FALLBACK_TOKENS", "1000")),
            temperature=float(os.getenv("LEGAL_ASSISTANT_TEMPERATURE", "0.3")),
            top_p=float(os.getenv("LEGAL_ASSISTANT_TOP_P", "0.9")),
            frequency_penalty=float(os.getenv("LEGAL_ASSISTANT_FREQUENCY_PENALTY", "0.1")),
            presence_penalty=float(os.getenv("LEGAL_ASSISTANT_PRESENCE_PENALTY", "0.1")),
            top_k=int(os.getenv("LEGAL_ASSISTANT_TOP_K", "5")),
            max_sources=int(os.getenv("LEGAL_ASSISTANT_MAX_SOURCES", "3")),
            arabic_threshold=float(os.getenv("LEGAL_ASSISTANT_ARABIC_THRESHOLD", "0.3")),
            max_file_size=int(os.getenv("LEGAL_ASSISTANT_MAX_FILE_SIZE", "10485760")),
            allowed_extensions=os.getenv("LEGAL_ASSISTANT_ALLOWED_EXTENSIONS", ".pdf,.doc,.docx,.txt").split(","),
            media_url=os.getenv("LEGAL_ASSISTANT_MEDIA_URL", "/media/"),
            media_root=os.getenv("LEGAL_ASSISTANT_MEDIA_ROOT", "media"),
            session_cookie_age=int(os.getenv("LEGAL_ASSISTANT_SESSION_COOKIE_AGE", "3600")),
            high_quality_threshold=int(os.getenv("LEGAL_ASSISTANT_HIGH_QUALITY_THRESHOLD", "200"))
        )


# System Prompts (copied from Django views)
SYSTEM_PROMPTS = {
    "arabic": """أنت مساعد قانوني ذكي ومتخصص في القانون السعودي والعربي. مهمتك:

1. استخدم السياق القانوني المقدم للإجابة بدقة ومهنية
2. إذا لم يحتوي السياق على معلومات ذات صلة، قل ذلك بوضوح
3. قدم معلومات قانونية دقيقة بناءً على الوثائق المقدمة
4. استخدم لغة قانونية واضحة ومفهومة
5. إذا كان السؤال يتعلق بقانون سعودي، ركز على الأنظمة السعودية
6. قدم نصائح عملية ومفيدة
7. أجب باللغة العربية فقط
8. إذا كان هناك معلومات من محادثة سابقة، استخدمها للسياق

تذكر: أنت مساعد قانوني محترف، لذا قدم إجابات موثوقة ومفيدة.""",

    "english": """You are an intelligent legal assistant specializing in Saudi and international law. Your mission:

1. Use the provided legal context to answer accurately and professionally
2. If the context doesn't contain relevant information, say so clearly
3. Provide accurate legal information based on the provided documents
4. Use clear and understandable legal language
5. If the question relates to Saudi law, focus on Saudi regulations
6. Provide practical and useful advice
7. Respond in English only
8. If there's information from previous conversation, use it for context

Remember: You are a professional legal assistant, so provide reliable and helpful answers.""",

    "arabic_fallback": "أنت مساعد قانوني مفيد متخصص في القانون السعودي. أجب باللغة العربية فقط.",
    
    "english_fallback": "You are a helpful legal assistant specializing in Saudi law."
}

# User Prompt Templates (copied from Django views)
USER_PROMPT_TEMPLATES = {
    "arabic": """المحادثة السابقة:
{conversation_context}

السياق من الوثائق القانونية:
{context_text}

السؤال الحالي: {question}

يرجى تقديم إجابة مفيدة ودقيقة بناءً على السياق القانوني المقدم أعلاه. إذا كان السؤال يتعلق بقانون سعودي، ركز على الأنظمة السعودية المعمول بها.""",

    "english": """Previous conversation:
{conversation_context}

Context from legal documents:
{context_text}

Current question: {question}

Please provide a helpful and accurate answer based on the legal context provided above. If the question relates to Saudi law, focus on applicable Saudi regulations.""",

    "arabic_simplified": """السؤال: {question}

يرجى تقديم إجابة قانونية مفيدة بناءً على المعرفة القانونية العامة والقانون السعودي.""",

    "english_simplified": """Question: {question}

Please provide a helpful legal answer based on general legal knowledge and Saudi law.""",

    "arabic_no_context": """السؤال: {question}

يرجى تقديم إجابة قانونية عامة. ملاحظة: لم تتوفر معلومات سياقية محددة من الوثائق.""",

    "english_no_context": """Question: {question}

Please provide a general legal answer. Note: No specific document context was available."""
}

# Error Messages (copied from Django views)
ERROR_MESSAGES = {
    "arabic": {
        "question_required": "السؤال مطلوب",
        "openai_not_configured": "مفتاح OpenAI API غير مُعد",
        "invalid_json": "بيانات JSON غير صحيحة",
        "general_error": "حدث خطأ: {error}",
        "no_relevant_docs": "لم يتم العثور على وثائق قانونية ذات صلة.",
        "context_note": "ملاحظة: بسبب قيود طول الوثيقة، هذه الإجابة مبنية على المعرفة القانونية العامة بدلاً من محتوى الوثيقة المحدد."
    },
    "english": {
        "question_required": "Question is required",
        "openai_not_configured": "OpenAI API key not configured",
        "invalid_json": "Invalid JSON data",
        "general_error": "An error occurred: {error}",
        "no_relevant_docs": "No relevant legal documents found.",
        "context_note": "Note: Due to document length limitations, this answer is based on general legal knowledge rather than specific document content."
    }
}

# Quality Assessment Labels
QUALITY_LABELS = {
    "high": "عالية",
    "medium": "متوسطة", 
    "low": "منخفضة"
}

# Sample Questions (copied from Django templates)
SAMPLE_QUESTIONS = {
    "employment-rights": {
        "ar": "ما هي حقوقي في عقد العمل؟",
        "en": "What are my rights in an employment contract?"
    },
    "file-lawsuit": {
        "ar": "كيف أرفع دعوى قضائية؟",
        "en": "How do I file a lawsuit?"
    },
    "rental-conditions": {
        "ar": "ما هي شروط الإيجار القانونية؟",
        "en": "What are the legal rental conditions?"
    },
    "commercial-rights": {
        "ar": "كيف أحمي حقوقي التجارية؟",
        "en": "How do I protect my commercial rights?"
    },
    "consumer-rights": {
        "ar": "ما هي حقوق المستهلك؟",
        "en": "What are consumer rights?"
    },
    "submit-complaint": {
        "ar": "كيف أتقدم بشكوى رسمية؟",
        "en": "How do I submit an official complaint?"
    }
}

# Welcome Messages
WELCOME_MESSAGES = {
    "arabic": "مرحباً! أنا مساعدك القانوني الذكي. يمكنني مساعدتك في الأسئلة المتعلقة بالوثائق القانونية والعقود والمسائل القانونية. ماذا تريد أن تعرف؟",
    "english": "Hello! I'm your legal AI assistant. I can help you with questions about legal documents, contracts, and legal matters. What would you like to know?"
}

# File Upload Messages
FILE_UPLOAD_MESSAGES = {
    "arabic": {
        "success": "تم رفع الملف بنجاح",
        "error": "خطأ في رفع الملف: {error}",
        "type_not_supported": "نوع الملف غير مدعوم",
        "size_too_large": "حجم الملف كبير جداً",
        "success_hint": "تم رفع الملف بنجاح. يمكنك الآن معالجة الوثيقة."
    },
    "english": {
        "success": "File uploaded successfully",
        "error": "Error uploading file: {error}",
        "type_not_supported": "File type not supported",
        "size_too_large": "File size too large",
        "success_hint": "File uploaded successfully. You can now process the document."
    }
}

# Voice Recognition Messages
VOICE_MESSAGES = {
    "arabic": "التعرف على الصوت غير متاح في متصفحك الحالي",
    "english": "Voice recognition is not available in your current browser"
}

# Export Messages
EXPORT_MESSAGES = {
    "arabic": {
        "no_history": "لا يوجد تاريخ محادثة للتصدير",
        "exporting": "جاري تصدير الوثيقة..."
    },
    "english": {
        "no_history": "No chat history to export",
        "exporting": "Exporting document..."
    }
}

# Smart Form Notification
SMART_FORM_NOTIFICATION = {
    "arabic": "استخدم النموذج الذكي أدناه للحصول على إجابات سريعة على الأسئلة القانونية الشائعة",
    "english": "Use the smart form below to get quick answers to common legal questions"
}

# Quality Text Messages
QUALITY_TEXT_MESSAGES = {
    "arabic": {
        "high": "إجابة عالية الجودة بناءً على الوثائق القانونية",
        "medium": "إجابة متوسطة الجودة بناءً على المعرفة العامة",
        "low": "إجابة عامة - يوصى بمراجعة محامٍ متخصص"
    },
    "english": {
        "high": "High quality answer based on legal documents",
        "medium": "Medium quality answer based on general knowledge", 
        "low": "General answer - recommend consulting a specialized lawyer"
    }
}


def get_config() -> LegalAssistantConfig:
    """Get the legal assistant configuration"""
    return LegalAssistantConfig.from_env()


def get_system_prompt(language: str) -> str:
    """Get system prompt for the given language"""
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["english"])


def get_user_prompt_template(language: str, simplified: bool = False, no_context: bool = False) -> str:
    """Get user prompt template for the given language"""
    if no_context:
        key = f"{language}_no_context"
    elif simplified:
        key = f"{language}_simplified"
    else:
        key = language
    
    return USER_PROMPT_TEMPLATES.get(key, USER_PROMPT_TEMPLATES["english"])


def get_error_message(language: str, error_type: str, **kwargs) -> str:
    """Get error message for the given language and error type"""
    message = ERROR_MESSAGES.get(language, ERROR_MESSAGES["english"]).get(error_type, "Unknown error")
    return message.format(**kwargs)


def get_sample_questions(language: str = "en") -> Dict[str, str]:
    """Get sample questions for the given language"""
    return {key: questions.get(language, questions["en"]) for key, questions in SAMPLE_QUESTIONS.items()}


def get_welcome_message(language: str) -> str:
    """Get welcome message for the given language"""
    return WELCOME_MESSAGES.get(language, WELCOME_MESSAGES["english"])


def get_file_upload_message(language: str, message_type: str, **kwargs) -> str:
    """Get file upload message for the given language and message type"""
    messages = FILE_UPLOAD_MESSAGES.get(language, FILE_UPLOAD_MESSAGES["english"])
    message = messages.get(message_type, "Unknown message")
    return message.format(**kwargs)


def get_quality_text(language: str, quality: str) -> str:
    """Get quality text for the given language and quality level"""
    return QUALITY_TEXT_MESSAGES.get(language, QUALITY_TEXT_MESSAGES["english"]).get(quality, "Unknown quality")

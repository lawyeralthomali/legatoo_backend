# Legal Assistant Configuration Keys Integration

## Overview
Successfully copied and integrated all configuration keys from the Django legal assistant app into the FastAPI application.

## 🔑 Configuration Keys Copied

### 1. API Keys
- **`OPENAI_API_KEY`** - OpenAI API key for AI functionality
- **`GOOGLE_API_KEY`** - Google API key for enhanced text extraction (optional)

### 2. Model Configuration
- **`LEGAL_ASSISTANT_DEFAULT_MODEL`** - Default model (gpt-4)
- **`LEGAL_ASSISTANT_FALLBACK_MODEL`** - Fallback model (gpt-3.5-turbo)
- **`LEGAL_ASSISTANT_EMBEDDING_MODEL`** - Embedding model (text-embedding-3-small)

### 3. Token Configuration
- **`LEGAL_ASSISTANT_MAX_TOKENS`** - Max tokens per response (1500)
- **`LEGAL_ASSISTANT_MAX_CONTEXT_TOKENS`** - Max context tokens (8000)
- **`LEGAL_ASSISTANT_MAX_FALLBACK_TOKENS`** - Max fallback tokens (1000)

### 4. AI Parameters
- **`LEGAL_ASSISTANT_TEMPERATURE`** - Temperature (0.3)
- **`LEGAL_ASSISTANT_TOP_P`** - Top P (0.9)
- **`LEGAL_ASSISTANT_FREQUENCY_PENALTY`** - Frequency penalty (0.1)
- **`LEGAL_ASSISTANT_PRESENCE_PENALTY`** - Presence penalty (0.1)

### 5. Search Configuration
- **`LEGAL_ASSISTANT_TOP_K`** - Top K chunks (5)
- **`LEGAL_ASSISTANT_MAX_SOURCES`** - Max sources (3)

### 6. Language Detection
- **`LEGAL_ASSISTANT_ARABIC_THRESHOLD`** - Arabic detection threshold (0.3)

### 7. File Upload Configuration
- **`LEGAL_ASSISTANT_MAX_FILE_SIZE`** - Max file size (10MB)
- **`LEGAL_ASSISTANT_ALLOWED_EXTENSIONS`** - Allowed extensions (.pdf, .doc, .docx, .txt)

### 8. Quality Assessment
- **`LEGAL_ASSISTANT_HIGH_QUALITY_THRESHOLD`** - High quality threshold (200)

## 📝 System Prompts Copied

### Arabic System Prompt
```
أنت مساعد قانوني ذكي ومتخصص في القانون السعودي والعربي. مهمتك:

1. استخدم السياق القانوني المقدم للإجابة بدقة ومهنية
2. إذا لم يحتوي السياق على معلومات ذات صلة، قل ذلك بوضوح
3. قدم معلومات قانونية دقيقة بناءً على الوثائق المقدمة
4. استخدم لغة قانونية واضحة ومفهومة
5. إذا كان السؤال يتعلق بقانون سعودي، ركز على الأنظمة السعودية
6. قدم نصائح عملية ومفيدة
7. أجب باللغة العربية فقط
8. إذا كان هناك معلومات من محادثة سابقة، استخدمها للسياق

تذكر: أنت مساعد قانوني محترف، لذا قدم إجابات موثوقة ومفيدة.
```

### English System Prompt
```
You are an intelligent legal assistant specializing in Saudi and international law. Your mission:

1. Use the provided legal context to answer accurately and professionally
2. If the context doesn't contain relevant information, say so clearly
3. Provide accurate legal information based on the provided documents
4. Use clear and understandable legal language
5. If the question relates to Saudi law, focus on Saudi regulations
6. Provide practical and useful advice
7. Respond in English only
8. If there's information from previous conversation, use it for context

Remember: You are a professional legal assistant, so provide reliable and helpful answers.
```

## 💬 User Prompt Templates Copied

### Arabic Templates
- **Full Context**: Includes conversation history and document context
- **Simplified**: Basic question without complex context
- **No Context**: General legal answer when no documents available

### English Templates
- **Full Context**: Includes conversation history and document context
- **Simplified**: Basic question without complex context
- **No Context**: General legal answer when no documents available

## 🚨 Error Messages Copied

### Arabic Error Messages
- **`question_required`**: "السؤال مطلوب"
- **`openai_not_configured`**: "مفتاح OpenAI API غير مُعد"
- **`invalid_json`**: "بيانات JSON غير صحيحة"
- **`general_error`**: "حدث خطأ: {error}"
- **`no_relevant_docs`**: "لم يتم العثور على وثائق قانونية ذات صلة."
- **`context_note`**: "ملاحظة: بسبب قيود طول الوثيقة، هذه الإجابة مبنية على المعرفة القانونية العامة بدلاً من محتوى الوثيقة المحدد."

### English Error Messages
- **`question_required`**: "Question is required"
- **`openai_not_configured`**: "OpenAI API key not configured"
- **`invalid_json`**: "Invalid JSON data"
- **`general_error`**: "An error occurred: {error}"
- **`no_relevant_docs`**: "No relevant legal documents found."
- **`context_note`**: "Note: Due to document length limitations, this answer is based on general legal knowledge rather than specific document content."

## 📋 Sample Questions Copied

### Employment Rights
- **Arabic**: "ما هي حقوقي في عقد العمل؟"
- **English**: "What are my rights in an employment contract?"

### File Lawsuit
- **Arabic**: "كيف أرفع دعوى قضائية؟"
- **English**: "How do I file a lawsuit?"

### Rental Conditions
- **Arabic**: "ما هي شروط الإيجار القانونية؟"
- **English**: "What are the legal rental conditions?"

### Commercial Rights
- **Arabic**: "كيف أحمي حقوقي التجارية؟"
- **English**: "How do I protect my commercial rights?"

### Consumer Rights
- **Arabic**: "ما هي حقوق المستهلك؟"
- **English**: "What are consumer rights?"

### Submit Complaint
- **Arabic**: "كيف أتقدم بشكوى رسمية؟"
- **English**: "How do I submit an official complaint?"

## 🎯 Welcome Messages Copied

### Arabic Welcome
"مرحباً! أنا مساعدك القانوني الذكي. يمكنني مساعدتك في الأسئلة المتعلقة بالوثائق القانونية والعقود والمسائل القانونية. ماذا تريد أن تعرف؟"

### English Welcome
"Hello! I'm your legal AI assistant. I can help you with questions about legal documents, contracts, and legal matters. What would you like to know?"

## 📁 File Upload Messages Copied

### Arabic Messages
- **`success`**: "تم رفع الملف بنجاح"
- **`error`**: "خطأ في رفع الملف: {error}"
- **`type_not_supported`**: "نوع الملف غير مدعوم"
- **`size_too_large`**: "حجم الملف كبير جداً"
- **`success_hint`**: "تم رفع الملف بنجاح. يمكنك الآن معالجة الوثيقة."

### English Messages
- **`success`**: "File uploaded successfully"
- **`error`**: "Error uploading file: {error}"
- **`type_not_supported`**: "File type not supported"
- **`size_too_large`**: "File size too large"
- **`success_hint`**: "File uploaded successfully. You can now process the document."

## 🔧 Implementation Details

### Configuration File
- **Location**: `app/config/legal_assistant.py`
- **Type**: Pydantic BaseSettings
- **Environment Variables**: All keys can be set via environment variables
- **Default Values**: All Django defaults preserved

### Service Integration
- **Location**: `app/services/legal_assistant_service.py`
- **Usage**: All methods now use configuration values
- **Dynamic**: Configuration loaded at runtime

### Router Integration
- **Location**: `app/routes/legal_assistant_router.py`
- **Usage**: Error messages and validation use configuration
- **Endpoints**: New endpoints for sample questions and welcome messages

## 🚀 New API Endpoints

### Sample Questions
```
GET /api/v1/legal-assistant/sample-questions?language=en
GET /api/v1/legal-assistant/sample-questions?language=ar
```

### Welcome Message
```
GET /api/v1/legal-assistant/welcome-message?language=en
GET /api/v1/legal-assistant/welcome-message?language=ar
```

## 📊 Configuration Usage Examples

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
GOOGLE_API_KEY=your_google_api_key_here
LEGAL_ASSISTANT_DEFAULT_MODEL=gpt-4
LEGAL_ASSISTANT_MAX_TOKENS=1500
LEGAL_ASSISTANT_TEMPERATURE=0.3
LEGAL_ASSISTANT_MAX_FILE_SIZE=10485760
```

### Programmatic Usage
```python
from app.config.legal_assistant import get_config, get_system_prompt

# Get configuration
config = get_config()
print(f"Default model: {config.default_model}")
print(f"Max tokens: {config.max_tokens}")

# Get system prompt
arabic_prompt = get_system_prompt("arabic")
english_prompt = get_system_prompt("english")
```

## ✅ Benefits

### 1. Complete Feature Parity
- All Django configuration keys preserved
- Same behavior and responses
- Identical user experience

### 2. Enhanced Flexibility
- Environment variable configuration
- Runtime configuration loading
- Easy deployment customization

### 3. Better Organization
- Centralized configuration
- Type-safe settings
- Clear documentation

### 4. Improved Maintainability
- Single source of truth
- Easy to update prompts
- Consistent error handling

## 🎉 Conclusion

All configuration keys from the Django legal assistant have been successfully copied and integrated into the FastAPI application:

- ✅ **API Keys**: OpenAI and Google API keys
- ✅ **Model Configuration**: All model settings
- ✅ **Token Management**: Token limits and thresholds
- ✅ **AI Parameters**: Temperature, penalties, etc.
- ✅ **System Prompts**: Arabic and English prompts
- ✅ **User Templates**: All prompt templates
- ✅ **Error Messages**: Bilingual error messages
- ✅ **Sample Questions**: Common legal questions
- ✅ **Welcome Messages**: Bilingual welcome messages
- ✅ **File Upload**: Upload validation and messages
- ✅ **Quality Assessment**: Response quality thresholds

The FastAPI legal assistant now has complete feature parity with the Django version while providing enhanced configurability and maintainability.

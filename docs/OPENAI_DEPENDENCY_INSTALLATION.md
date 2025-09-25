# OpenAI Dependency Installation Guide

## Issue
The legal assistant is showing the error:
```json
{
  "detail": "OpenAI not installed. Please install: pip install openai"
}
```

This occurs because the required AI dependencies are not installed on the system.

## Required Dependencies

The legal assistant requires these packages for full functionality:

### Core AI Dependencies
- **`openai==1.3.7`** - OpenAI API client for GPT models
- **`tiktoken==0.5.1`** - Token counting for text processing
- **`numpy==1.24.3`** - Numerical computations for similarity calculations

### Optional Dependencies
- **`PyMuPDF==1.23.8`** - PDF processing (for document uploads)

## Installation Methods

### Method 1: Install from requirements.txt (Recommended)
```bash
python -m pip install -r requirements.txt
```

### Method 2: Install Individual Packages
```bash
python -m pip install openai==1.3.7
python -m pip install tiktoken==0.5.1
python -m pip install numpy==1.24.3
python -m pip install PyMuPDF==1.23.8
```

### Method 3: Install All at Once
```bash
python -m pip install openai==1.3.7 tiktoken==0.5.1 numpy==1.24.3 PyMuPDF==1.23.8
```

## Environment Setup

### Required Environment Variable
After installing the dependencies, you need to set the OpenAI API key:

```bash
# Windows (Command Prompt)
set OPENAI_API_KEY=your_openai_api_key_here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your_openai_api_key_here"

# Linux/macOS
export OPENAI_API_KEY=your_openai_api_key_here
```

### .env File (Alternative)
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

## Verification

### Test Installation
```python
# Test OpenAI installation
try:
    import openai
    print("✅ OpenAI installed successfully")
except ImportError:
    print("❌ OpenAI not installed")

# Test tiktoken installation
try:
    import tiktoken
    print("✅ tiktoken installed successfully")
except ImportError:
    print("❌ tiktoken not installed")

# Test numpy installation
try:
    import numpy
    print("✅ numpy installed successfully")
except ImportError:
    print("❌ numpy not installed")
```

### Test API Key
```python
import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI API key configured")
else:
    print("❌ OpenAI API key not found")
```

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Try with --user flag
python -m pip install --user openai==1.3.7
```

#### 2. Network Issues
```bash
# Try with --trusted-host
python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org openai==1.3.7
```

#### 3. Virtual Environment Issues
```bash
# Activate virtual environment first
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Then install
python -m pip install openai==1.3.7
```

#### 4. Python Version Issues
```bash
# Check Python version
python --version

# Should be Python 3.8 or higher
```

### Alternative Installation Methods

#### Using Conda
```bash
conda install -c conda-forge openai
conda install -c conda-forge numpy
pip install tiktoken
```

#### Using Poetry
```bash
poetry add openai==1.3.7
poetry add tiktoken==0.5.1
poetry add numpy==1.24.3
```

## Testing the Legal Assistant

### 1. Start the Server
```bash
python start_server.py
```

### 2. Check Status
```bash
curl http://localhost:8000/api/v1/legal-assistant/status
```

Expected response:
```json
{
  "status": "active",
  "dependencies": {
    "openai": true,
    "tiktoken": true,
    "numpy": true
  },
  "features_available": [
    "language_detection",
    "basic_chat",
    "ai_chat",
    "document_processing",
    "semantic_search"
  ],
  "models_available": [
    "gpt-3.5-turbo",
    "gpt-4",
    "text-embedding-3-small"
  ]
}
```

### 3. Test Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/legal-assistant/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "What are the requirements for employment contracts?",
    "history": []
  }'
```

## Graceful Degradation

The legal assistant is designed to work even without all dependencies:

### Without OpenAI
- ✅ Language detection works
- ✅ Basic chat interface works
- ❌ AI responses not available
- ❌ Document processing limited

### Without tiktoken
- ✅ OpenAI functionality works
- ✅ Token counting uses fallback estimation
- ⚠️ Less accurate token counting

### Without numpy
- ✅ OpenAI functionality works
- ✅ Similarity search uses fallback implementation
- ⚠️ Slightly slower similarity calculations

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "start_server.py"]
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
GOOGLE_API_KEY=your_google_api_key_here
LEGAL_ASSISTANT_DEFAULT_MODEL=gpt-4
LEGAL_ASSISTANT_MAX_TOKENS=1500
LEGAL_ASSISTANT_TEMPERATURE=0.3
```

## Conclusion

To fix the "OpenAI not installed" error:

1. **Install Dependencies**: `python -m pip install -r requirements.txt`
2. **Set API Key**: `export OPENAI_API_KEY=your_key_here`
3. **Restart Server**: `python start_server.py`
4. **Test Endpoint**: Check `/api/v1/legal-assistant/status`

The legal assistant will then have full AI functionality with GPT-4, semantic search, and document processing capabilities.

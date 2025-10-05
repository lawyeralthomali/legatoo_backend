# 🚀 Quick Start - Legal Laws Management API

## Get Started in 5 Minutes!

---

## ✅ Prerequisites

- Python 3.8+
- FastAPI application running
- JWT authentication token
- A legal PDF file to upload

---

## 📋 Step-by-Step Guide

### **Step 1: Apply Database Migration** (If not done yet)

```bash
# Backup your database first
cp app.db app.db.backup_$(date +%Y%m%d_%H%M%S)

# Run the migration
alembic upgrade head

# Verify
python -c "from app.models.legal_knowledge import LawSource, LawBranch, LawChapter; print('✅ Models loaded successfully!')"
```

### **Step 2: Start the Server**

```bash
# Option 1: Using run.py
python run.py

# Option 2: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Server will be available at:** `http://localhost:8000`

### **Step 3: Get Authentication Token**

```bash
# Login to get JWT token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

**Save the `access_token` from the response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### **Step 4: Upload Your First Law**

```bash
# Upload a legal PDF
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "law_name=قانون العمل السعودي" \
  -F "law_type=law" \
  -F "jurisdiction=المملكة العربية السعودية" \
  -F "issuing_authority=وزارة العمل" \
  -F "issue_date=2005-04-23" \
  -F "description=نظام العمل السعودي" \
  -F "pdf_file=@/path/to/your/law.pdf"
```

**✅ Expected Response:**
```json
{
  "success": true,
  "message": "Law uploaded and parsed successfully. Created 6 branches, 145 articles.",
  "data": {
    "law_source": {
      "id": 1,
      "name": "قانون العمل السعودي",
      "status": "processed",
      "branches": [
        {
          "id": 1,
          "branch_name": "علاقات العمل",
          "chapters": [
            {
              "chapter_name": "انتهاء عقد العمل",
              "articles": [...]
            }
          ]
        }
      ]
    }
  }
}
```

### **Step 5: View Your Law**

```bash
# Get complete hierarchy tree
curl -X GET "http://localhost:8000/api/v1/laws/1/tree" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Step 6: Analyze with AI** (Optional)

```bash
# Generate embeddings and extract keywords
curl -X POST "http://localhost:8000/api/v1/laws/1/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Step 7: Get Statistics**

```bash
# View law statistics
curl -X GET "http://localhost:8000/api/v1/laws/1/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🌐 Alternative: Using the Interactive API Documentation

### **Swagger UI:**

1. Open browser: `http://localhost:8000/docs`
2. Click **"Authorize"** button (top right)
3. Enter: `Bearer YOUR_TOKEN_HERE`
4. Click **"Authorize"**
5. Try endpoints directly in the browser!

### **ReDoc:**

- Open browser: `http://localhost:8000/redoc`
- Browse the complete API documentation

---

## 🐍 Python Script Example

```python
import requests

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. Upload law
with open("labor_law.pdf", "rb") as pdf_file:
    files = {"pdf_file": pdf_file}
    data = {
        "law_name": "Labor Law",
        "law_type": "law",
        "jurisdiction": "Saudi Arabia",
        "issuing_authority": "Ministry of Labor"
    }
    response = requests.post(f"{API_URL}/laws/upload", headers=headers, files=files, data=data)
    result = response.json()
    print(f"✅ Uploaded: {result['message']}")
    law_id = result['data']['law_source']['id']

# 2. Get tree
response = requests.get(f"{API_URL}/laws/{law_id}/tree", headers=headers)
tree = response.json()
print(f"✅ Branches: {tree['data']['law_source']['branches_count']}")

# 3. Get statistics
response = requests.get(f"{API_URL}/laws/{law_id}/statistics", headers=headers)
stats = response.json()
print(f"✅ Articles: {stats['data']['articles_count']}")

# 4. Analyze with AI
response = requests.post(f"{API_URL}/laws/{law_id}/analyze", headers=headers)
analysis = response.json()
print(f"✅ AI Analysis: {analysis['message']}")
```

---

## 📊 Common Operations

### **List All Laws**
```bash
curl -X GET "http://localhost:8000/api/v1/laws/?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Search Laws by Name**
```bash
curl -X GET "http://localhost:8000/api/v1/laws/?name=عمل" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Filter by Status**
```bash
curl -X GET "http://localhost:8000/api/v1/laws/?status=processed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Update Law Metadata**
```bash
curl -X PUT "http://localhost:8000/api/v1/laws/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "description=Updated description" \
  -F "last_update=2024-01-15"
```

### **Delete Law**
```bash
curl -X DELETE "http://localhost:8000/api/v1/laws/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Testing with Sample Data

### **Create Test User (if needed)**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'
```

### **Test with Sample PDF**

If you don't have a legal PDF, create a simple test PDF:

```bash
# Install required package
pip install reportlab

# Create test PDF
python << 'EOF'
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Create a simple PDF
c = canvas.Canvas("test_law.pdf", pagesize=A4)
c.setFont("Helvetica", 16)
c.drawString(100, 750, "Test Law Document")
c.setFont("Helvetica", 12)
c.drawString(100, 700, "Branch 1: Employment Relations")
c.drawString(100, 680, "Chapter 1: Contract Duration")
c.drawString(100, 660, "Article 1: An employment contract shall be...")
c.save()
print("✅ Created test_law.pdf")
EOF

# Upload the test PDF
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "law_name=Test Law" \
  -F "law_type=law" \
  -F "jurisdiction=Test" \
  -F "pdf_file=@test_law.pdf"
```

---

## ⚠️ Troubleshooting

### **Error: "Duplicate file detected"**
```bash
# The file hash already exists
# Solution: Either use a different file or delete the existing law first
```

### **Error: "No text could be extracted from the PDF"**
```bash
# The PDF might be image-based (scanned)
# Solution: Install Tesseract OCR for scanned PDFs
sudo apt-get install tesseract-ocr tesseract-ocr-ara  # Linux
brew install tesseract tesseract-lang  # macOS
```

### **Error: "Unauthorized"**
```bash
# Your token might be expired or invalid
# Solution: Get a new token by logging in again
```

### **Error: "Law with ID X not found"**
```bash
# The law doesn't exist
# Solution: Verify the law_id by listing all laws
curl -X GET "http://localhost:8000/api/v1/laws/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 Next Steps

1. **Read Full Documentation:**
   - See `LEGAL_LAWS_API_DOCUMENTATION.md` for complete API reference

2. **Explore Advanced Features:**
   - Reparse laws: `/laws/{id}/reparse`
   - AI analysis: `/laws/{id}/analyze`
   - Statistics: `/laws/{id}/statistics`

3. **Integrate with Your Frontend:**
   - Use the API endpoints in your React/Vue/Angular app
   - Implement law browsing interface
   - Add search and filter functionality

4. **Set Up Production:**
   - Configure production database
   - Set up proper authentication
   - Enable SSL/HTTPS
   - Set up backup schedules

---

## ✅ Success Checklist

- [ ] Database migration applied
- [ ] Server running successfully
- [ ] Authentication token obtained
- [ ] First law uploaded successfully
- [ ] Can view law tree structure
- [ ] Can list all laws
- [ ] Can update law metadata
- [ ] AI analysis working (optional)
- [ ] Statistics endpoint responding

---

## 🎉 You're Ready!

You now have a complete legal laws management API with:
- ✅ Automatic PDF parsing
- ✅ Hierarchical structure extraction
- ✅ Duplicate prevention
- ✅ AI integration
- ✅ Comprehensive CRUD operations

**Happy coding! 🚀**

---

## 📞 Support

- **API Documentation:** http://localhost:8000/docs
- **Full Guide:** `LEGAL_LAWS_API_DOCUMENTATION.md`
- **Implementation Summary:** `LEGAL_LAWS_API_SUMMARY.md`
- **Schema Changes:** `LEGAL_KNOWLEDGE_SCHEMA_UPDATE.md`

**Version:** 1.0.0  
**Last Updated:** October 5, 2025

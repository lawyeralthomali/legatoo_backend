# TXT File Upload Support for Legal Cases

## Summary
Added support for `.txt` file uploads to the legal case ingestion system, allowing users to upload plain text files in addition to PDF and DOCX formats.

## Changes Made

### 1. Router Updates (`app/routes/legal_cases_router.py`)

#### Updated File Parameter Description
- **Line 28**: Changed description from "PDF or DOCX file" to "PDF, DOCX, or TXT file"

#### Updated Docstring
- **Lines 49-57**: Updated documentation to reflect TXT support
  - Changed "PDF or DOCX file" to "PDF, DOCX, or TXT file"
  - Updated supported formats list to include TXT

#### Updated File Validation
- **Line 79**: Added `'txt'` to the list of allowed file extensions
- **Lines 82-84**: Updated error messages to mention TXT support

### 2. Service Updates (`app/services/legal_case_ingestion_service.py`)

#### Updated Class Docstring
- **Line 43**: Changed from "PDF/DOCX files" to "PDF/DOCX/TXT files"

#### Updated `extract_text()` Method
- **Lines 182-202**: 
  - Updated docstring to mention TXT support
  - Added condition to handle `.txt` file extension
  - Routes to new `_extract_txt_text()` method

#### Added New Method: `_extract_txt_text()`
- **Lines 281-314**: New method for extracting text from TXT files
  - Implements intelligent encoding detection for Arabic text
  - Tries multiple encodings in order:
    1. **UTF-8** (most common, modern standard)
    2. **Windows-1256** (Arabic encoding fallback)
    3. **ISO-8859-1** (final fallback)
  - Logs which encoding was successfully used
  - Provides detailed error messages if extraction fails

## Features

### Multi-Encoding Support
The TXT extraction includes robust encoding detection to handle various Arabic text encodings:

```python
# UTF-8 (primary)
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Windows-1256 (Arabic fallback)
with open(file_path, 'r', encoding='windows-1256') as f:
    text = f.read()

# ISO-8859-1 (final fallback)
with open(file_path, 'r', encoding='iso-8859-1') as f:
    text = f.read()
```

### Logging
Each extraction method logs:
- Number of characters extracted
- Encoding used (for TXT files)
- Any warnings or errors encountered

## API Usage

### Endpoint
`POST /api/v1/legal-cases/upload`

### Supported File Types
- `.pdf` - PDF documents
- `.docx`, `.doc` - Microsoft Word documents
- `.txt` - Plain text files (NEW)

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/legal-cases/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@legal_case.txt" \
  -F "title=Legal Case Title" \
  -F "case_number=123/2024" \
  -F "jurisdiction=الرياض" \
  -F "court_name=المحكمة العامة" \
  -F "case_type=مدني"
```

### Example Response
```json
{
  "success": true,
  "message": "Legal case ingested successfully",
  "data": {
    "knowledge_document_id": 45,
    "legal_case_id": 23,
    "case_number": "123/2024",
    "title": "Legal Case Title",
    "file_path": "uploads/legal_cases/20241006_123456_abc123def456.txt",
    "file_hash": "abc123def456...",
    "text_length": 5432,
    "sections_found": ["summary", "facts", "ruling", "legal_basis"],
    "sections_count": 4
  },
  "errors": []
}
```

## Processing Flow

1. **File Upload & Validation**
   - Validates file extension (`.pdf`, `.docx`, `.doc`, `.txt`)
   - Checks file is not empty
   - Calculates SHA-256 hash for duplicate detection

2. **Text Extraction**
   - For TXT: Multi-encoding detection (UTF-8 → Windows-1256 → ISO-8859-1)
   - For PDF: PyMuPDF or pdfplumber
   - For DOCX: python-docx

3. **Section Segmentation**
   - Detects Arabic section markers:
     - ملخص → summary
     - الوقائع → facts
     - الحجج → arguments
     - الحكم → ruling
     - الأساس القانوني → legal_basis

4. **Database Storage**
   - Creates `KnowledgeDocument` record
   - Creates `LegalCase` record
   - Creates `CaseSection` records for each detected section
   - Updates status to 'processed'

## Error Handling

### Invalid File Type
```json
{
  "success": false,
  "message": "Invalid file format. Only PDF, DOCX, and TXT are supported.",
  "data": null,
  "errors": [
    {
      "field": "file",
      "message": "Only PDF, DOCX, and TXT files are supported"
    }
  ]
}
```

### Encoding Issues
If all encoding attempts fail, the service will raise a `RuntimeError` with details about the failure.

## Benefits

1. **Flexibility**: Users can now upload plain text files directly
2. **Arabic Support**: Robust encoding detection for Arabic text files
3. **Consistency**: Same processing pipeline for all file types
4. **Logging**: Clear logs showing which encoding was used
5. **Error Handling**: Graceful fallback between different encodings

## Testing Recommendations

1. **UTF-8 TXT File**
   - Create a TXT file with Arabic text in UTF-8 encoding
   - Upload and verify successful extraction

2. **Windows-1256 TXT File**
   - Create a TXT file with Arabic text in Windows-1256 encoding
   - Upload and verify fallback encoding works

3. **Mixed Content**
   - Upload TXT file with both Arabic and English text
   - Verify section detection works correctly

4. **Large Files**
   - Test with large TXT files (> 1MB)
   - Verify performance is acceptable

## Compatibility

- **No Breaking Changes**: All existing PDF and DOCX functionality remains unchanged
- **Backward Compatible**: Existing API calls continue to work
- **Model Compatible**: Works with the updated `legal_knowledge.py` model

## Next Steps (Optional Enhancements)

1. **Character Encoding Auto-Detection**
   - Consider using `chardet` library for automatic encoding detection
   - Would eliminate the need for manual fallback chain

2. **File Size Limits**
   - Consider adding explicit file size validation
   - Currently handled at file read level

3. **Rich Text Support**
   - Could add support for RTF files if needed
   - Would require additional library (`striprtf` or similar)

4. **Validation**
   - Add minimum text length validation for TXT files
   - Ensure quality of uploaded content

---

**Status**: ✅ Complete
**Date**: October 6, 2024
**Files Modified**: 2
**Linter Errors**: 0


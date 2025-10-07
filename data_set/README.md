# Updated JSON Upload System

## Overview

The JSON upload system has been updated to work with the new file structure in `data_set/files/` and handle both types of law structures.

## File Structure

```
data_set/
├── files/
│   ├── 1.json                           # Direct articles structure
│   └── extracted_legal_structure.json   # Hierarchical structure
├── batch_upload_json.py                 # Batch upload script
├── test_json_upload.py                  # Single file test
├── test_both_files.py                   # Test both files
└── convert_to_law_format.py             # Format converter
```

## Supported JSON Structures

### 1. Hierarchical Structure (extracted_legal_structure.json)
```json
{
  "law_sources": [
    {
      "name": "نظام العمل السعودي",
      "type": "law",
      "branches": [
        {
          "branch_number": "الأول",
          "branch_name": "التعريفات / الأحكام العامة",
          "chapters": [
            {
              "chapter_number": "الأول",
              "chapter_name": "التعريفات",
              "articles": [
                {
                  "article_number": "الأولى",
                  "title": "اسم النظام",
                  "content": "يسمى هذا النظام نظام العمل.",
                  "keywords": ["نظام العمل"]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 2. Direct Articles Structure (1.json)
```json
{
  "law_sources": [
    {
      "name": "اللائحة التنظيمية للجان إصلاح ذات البين",
      "type": "regulation",
      "articles": [
        {
          "article_number": "الأولى",
          "title": "تشكيل اللجنة واختصاصها",
          "content": "تشكل في كل منطقة بقرار من أمير المنطقة...",
          "keywords": ["تشكيل لجنة", "إصلاح ذات البين"]
        }
      ]
    }
  ]
}
```

## Updated Scripts

### 1. Batch Upload Script (`batch_upload_json.py`)
- ✅ **Updated path**: Now looks in `data_set/files/`
- ✅ **Enhanced validation**: Handles both structure types
- ✅ **Better error messages**: Clear feedback for different structures

**Usage:**
```bash
cd data_set
python batch_upload_json.py
```

### 2. Test Scripts
- ✅ **`test_json_upload.py`**: Tests single file upload
- ✅ **`test_both_files.py`**: Tests both files in sequence

**Usage:**
```bash
cd data_set
python test_both_files.py
```

### 3. Service Updates (`app/services/legal_laws_service.py`)
- ✅ **Dual structure support**: Handles both hierarchical and direct articles
- ✅ **Proper database mapping**: Creates correct relationships
- ✅ **Enhanced logging**: Better progress tracking

## Database Mapping

### Hierarchical Structure
```
LawSource → LawBranch → LawChapter → LawArticle
```

### Direct Articles Structure
```
LawSource → LawArticle (no branches/chapters)
```

## API Endpoint

**Endpoint:** `POST /api/v1/laws/upload-json`

**Features:**
- ✅ **Automatic structure detection**
- ✅ **Flexible validation**
- ✅ **Proper error handling**
- ✅ **Statistics reporting**

## Usage Examples

### 1. Test Both Files
```bash
cd data_set
python test_both_files.py
```

### 2. Batch Upload All Files
```bash
cd data_set
python batch_upload_json.py
```

### 3. Test Single File
```bash
cd data_set
python test_json_upload.py
```

## Validation Rules

### Required Fields
- `law_sources` array
- `name` and `type` in law source
- Valid `type`: 'law', 'regulation', 'code', 'directive', 'decree'

### Structure Validation
- **Hierarchical**: Must have `branches` → `chapters` → `articles`
- **Direct**: Must have `articles` directly under law source
- At least one article must exist

## Error Handling

The system provides clear error messages for:
- Invalid JSON format
- Missing required fields
- Invalid law types
- Empty structures
- File not found errors

## Ready to Use

All scripts are updated and ready to work with your new file structure! 🎉

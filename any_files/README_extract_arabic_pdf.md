# Arabic PDF Text Extraction Script

This script extracts Arabic text from PDF files using two different methods and compares their effectiveness.

## Features

- **Dual Extraction Methods**: Direct text extraction (PyMuPDF) and OCR extraction (Tesseract)
- **Arabic Text Processing**: Fixes Arabic text direction using `arabic-reshaper` and `python-bidi`
- **Comprehensive Logging**: Detailed logs showing extraction progress and character counts
- **Error Handling**: Graceful handling of missing dependencies and file issues
- **Output Files**: Saves results to `output_direct.txt` and `output_ocr.txt`

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR engine:
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr tesseract-ocr-ara`
   - **CentOS/RHEL**: `sudo yum install tesseract tesseract-langpack-ara`

## Usage

```bash
# Basic usage
python extract_arabic_pdf.py document.pdf

# Specify output directory
python extract_arabic_pdf.py document.pdf --output-dir ./results

# Help
python extract_arabic_pdf.py --help
```

## Output Files

- `output_direct.txt`: Text extracted using PyMuPDF (direct method)
- `output_ocr.txt`: Text extracted using Tesseract OCR
- `extraction.log`: Detailed extraction log with character counts and errors

## How It Works

1. **Direct Extraction**: Uses PyMuPDF to extract text directly from PDF structure
2. **OCR Extraction**: Converts PDF pages to images, then uses Tesseract with Arabic language support
3. **Text Processing**: Both methods apply Arabic text reshaping and bidirectional algorithm
4. **Comparison**: Logs show which method extracted more characters

## Error Handling

The script gracefully handles:
- Missing dependencies (continues with available methods)
- Invalid file paths
- Corrupted PDFs
- Tesseract installation issues
- File I/O errors

## Example Output

```
2024-01-15 10:30:00 - INFO - Starting Arabic PDF text extraction for: document.pdf
2024-01-15 10:30:01 - INFO - ✅ Direct extraction SUCCESS: 1,234 characters extracted
2024-01-15 10:30:15 - INFO - ✅ OCR extraction SUCCESS: 1,456 characters extracted
2024-01-15 10:30:15 - INFO - 🏆 OCR extraction yielded more text
```

## Tips

- OCR works better for scanned PDFs or images
- Direct extraction works better for text-based PDFs
- Higher DPI (300) improves OCR accuracy but increases processing time
- Check `extraction.log` for detailed debugging information





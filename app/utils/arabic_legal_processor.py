"""
Arabic Legal Document Processing Utilities

This module provides specialized utilities for processing Arabic legal documents,
following the principles of unified approach and separation of concerns.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, date

from .arabic_text_processor import ArabicTextProcessor
from .exceptions import AppException, ValidationException, NotFoundException

logger = logging.getLogger(__name__)


class ArabicLegalDocumentException(AppException):
    """Exception for Arabic legal document processing errors."""
    
    def __init__(
        self,
        message: str = "Arabic legal document processing failed",
        field: Optional[str] = None,
        document_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Arabic legal document exception.
        
        Args:
            message: Error message
            field: Field that caused the error
            document_path: Path to the document being processed
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="ARABIC_LEGAL_DOCUMENT_ERROR",
            field=field,
            details={"document_path": document_path, **(details or {})}
        )


class ArabicLegalPatterns:
    """Centralized patterns for Arabic legal document processing."""
    
    # Law source patterns
    LAW_NAME_PATTERNS = [
        r"نظام\s+(.+?)(?:\s+رقم|\s+لعام|\s+لسنة)",
        r"مرسوم\s+(.+?)(?:\s+رقم|\s+لعام|\s+لسنة)",
        r"قانون\s+(.+?)(?:\s+رقم|\s+لعام|\s+لسنة)",
        r"لائحة\s+(.+?)(?:\s+رقم|\s+لعام|\s+لسنة)",
        r"قرار\s+(.+?)(?:\s+رقم|\s+لعام|\s+لسنة)"
    ]
    
    LAW_TYPE_PATTERNS = [
        (r"نظام", "law"),
        (r"مرسوم", "decree"),
        (r"قانون", "law"),
        (r"لائحة", "regulation"),
        (r"قرار", "directive")
    ]
    
    ISSUING_AUTHORITY_PATTERNS = [
        r"وزارة\s+(.+?)(?:\s+و|\s+،|\s+\.|\s+\n)",
        r"هيئة\s+(.+?)(?:\s+و|\s+،|\s+\.|\s+\n)",
        r"مجلس\s+(.+?)(?:\s+و|\s+،|\s+\.|\s+\n)"
    ]
    
    DATE_PATTERNS = [
        r"لعام\s+(\d{4})",
        r"لسنة\s+(\d{4})",
        r"عام\s+(\d{4})",
        r"سنة\s+(\d{4})"
    ]
    
    # Article patterns
    ARTICLE_PATTERNS = [
        # Arabic ordinal numbers (الأولى، الثانية، الثالثة، etc.)
        r"المادة\s+(الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|الثالثة\s+عشرة|الرابعة\s+عشرة|الخامسة\s+عشرة|السادسة\s+عشرة|السابعة\s+عشرة|الثامنة\s+عشرة|التاسعة\s+عشرة|العشرون|الحادية\s+والعشرون|الثانية\s+والعشرون|الثالثة\s+والعشرون|الرابعة\s+والعشرون|الخامسة\s+والعشرون|السادسة\s+والعشرون|السابعة\s+والعشرون|الثامنة\s+والعشرون|التاسعة\s+والعشرون|الثلاثون|الحادية\s+والثلاثون|الثانية\s+والثلاثون|الثالثة\s+والثلاثون|الرابعة\s+والثلاثون|الخامسة\s+والثلاثون|السادسة\s+والثلاثون|السابعة\s+والثلاثون|الثامنة\s+والثلاثون|التاسعة\s+والثلاثون|الأربعون|الحادية\s+والأربعون|الثانية\s+والأربعون|الثالثة\s+والأربعون|الرابعة\s+والأربعون|الخامسة\s+والأربعون|السادسة\s+والأربعون|السابعة\s+والأربعون|الثامنة\s+والأربعون|التاسعة\s+والأربعون|الخمسون|الحادية\s+والخمسون|الثانية\s+والخمسون|الثالثة\s+والخمسون|الرابعة\s+والخمسون|الخامسة\s+والخمسون|السادسة\s+والخمسون|السابعة\s+والخمسون|الثامنة\s+والخمسون|التاسعة\s+والخمسون|الستون|الحادية\s+والستون|الثانية\s+والستون|الثالثة\s+والستون|الرابعة\s+والستون|الخامسة\s+والستون|السادسة\s+والستون|السابعة\s+والستون|الثامنة\s+والستون|التاسعة\s+والستون|السبعون|الحادية\s+والسبعون|الثانية\s+والسبعون|الثالثة\s+والسبعون|الرابعة\s+والسبعون|الخامسة\s+والسبعون|السادسة\s+والسبعون|السابعة\s+والسبعون|الثامنة\s+والسبعون|التاسعة\s+والسبعون|الثمانون|الحادية\s+والثمانون|الثانية\s+والثمانون|الثالثة\s+والثمانون|الرابعة\s+والثمانون|الخامسة\s+والثمانون|السادسة\s+والثمانون|السابعة\s+والثمانون|الثامنة\s+والثمانون|التاسعة\s+والثمانون|التسعون|الحادية\s+والتسعون|الثانية\s+والتسعون|الثالثة\s+والتسعون|الرابعة\s+والتسعون|الخامسة\s+والتسعون|السادسة\s+والتسعون|السابعة\s+والتسعون|الثامنة\s+والتسعون|التاسعة\s+والتسعون|المائة|الحادية\s+بعد\s+المائة|الثانية\s+بعد\s+المائة|الثالثة\s+بعد\s+المائة|الرابعة\s+بعد\s+المائة|الخامسة\s+بعد\s+المائة|السادسة\s+بعد\s+المائة|السابعة\s+بعد\s+المائة|الثامنة\s+بعد\s+المائة|التاسعة\s+بعد\s+المائة|المائتان|الحادية\s+بعد\s+المائتين|الثانية\s+بعد\s+المائتين|الثالثة\s+بعد\s+المائتين|الرابعة\s+بعد\s+المائتين|الخامسة\s+بعد\s+المائتين|السادسة\s+بعد\s+المائتين|السابعة\s+بعد\s+المائتين|الثامنة\s+بعد\s+المائتين|التاسعة\s+بعد\s+المائتين)[:\.]?\s*(.*?)(?=المادة\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|الثالثة\s+عشرة|الرابعة\s+عشرة|الخامسة\s+عشرة|السادسة\s+عشرة|السابعة\s+عشرة|الثامنة\s+عشرة|التاسعة\s+عشرة|العشرون|الحادية\s+والعشرون|الثانية\s+والعشرون|الثالثة\s+والعشرون|الرابعة\s+والعشرون|الخامسة\s+والعشرون|السادسة\s+والعشرون|السابعة\s+والعشرون|الثامنة\s+والعشرون|التاسعة\s+والعشرون|الثلاثون|الحادية\s+والثلاثون|الثانية\s+والثلاثون|الثالثة\s+والثلاثون|الرابعة\s+والثلاثون|الخامسة\s+والثلاثون|السادسة\s+والثلاثون|السابعة\s+والثلاثون|الثامنة\s+والثلاثون|التاسعة\s+والثلاثون|الأربعون|الحادية\s+والأربعون|الثانية\s+والأربعون|الثالثة\s+والأربعون|الرابعة\s+والأربعون|الخامسة\s+والأربعون|السادسة\s+والأربعون|السابعة\s+والأربعون|الثامنة\s+والأربعون|التاسعة\s+والأربعون|الخمسون|الحادية\s+والخمسون|الثانية\s+والخمسون|الثالثة\s+والخمسون|الرابعة\s+والخمسون|الخامسة\s+والخمسون|السادسة\s+والخمسون|السابعة\s+والخمسون|الثامنة\s+والخمسون|التاسعة\s+والخمسون|الستون|الحادية\s+والستون|الثانية\s+والستون|الثالثة\s+والستون|الرابعة\s+والستون|الخامسة\s+والستون|السادسة\s+والستون|السابعة\s+والستون|الثامنة\s+والستون|التاسعة\s+والستون|السبعون|الحادية\s+والسبعون|الثانية\s+والسبعون|الثالثة\s+والسبعون|الرابعة\s+والسبعون|الخامسة\s+والسبعون|السادسة\s+والسبعون|السابعة\s+والسبعون|الثامنة\s+والسبعون|التاسعة\s+والسبعون|الثمانون|الحادية\s+والثمانون|الثانية\s+والثمانون|الثالثة\s+والثمانون|الرابعة\s+والثمانون|الخامسة\s+والثمانون|السادسة\s+والثمانون|السابعة\s+والثمانون|الثامنة\s+والثمانون|التاسعة\s+والثمانون|التسعون|الحادية\s+والتسعون|الثانية\s+والتسعون|الثالثة\s+والتسعون|الرابعة\s+والتسعون|الخامسة\s+والتسعون|السادسة\s+والتسعون|السابعة\s+والتسعون|الثامنة\s+والتسعون|التاسعة\s+والتسعون|المائة|الحادية\s+بعد\s+المائة|الثانية\s+بعد\s+المائة|الثالثة\s+بعد\s+المائة|الرابعة\s+بعد\s+المائة|الخامسة\s+بعد\s+المائة|السادسة\s+بعد\s+المائة|السابعة\s+بعد\s+المائة|الثامنة\s+بعد\s+المائة|التاسعة\s+بعد\s+المائة|المائتان|الحادية\s+بعد\s+المائتين|الثانية\s+بعد\s+المائتين|الثالثة\s+بعد\s+المائتين|الرابعة\s+بعد\s+المائتين|الخامسة\s+بعد\s+المائتين|السادسة\s+بعد\s+المائتين|السابعة\s+بعد\s+المائتين|الثامنة\s+بعد\s+المائتين|التاسعة\s+بعد\s+المائتين)|$)",
        # Numeric patterns (original)
        r"المادة\s+(\d+)[:\.]?\s*(.*?)(?=المادة\s+\d+|$)",
        r"مادة\s+(\d+)[:\.]?\s*(.*?)(?=مادة\s+\d+|$)",
        r"الفقرة\s+(\d+)[:\.]?\s*(.*?)(?=الفقرة\s+\d+|$)",
        r"البند\s+(\d+)[:\.]?\s*(.*?)(?=البند\s+\d+|$)"
    ]
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        r"نظام\s+(.+?)(?:\s+رقم|\s+لعام)",
        r"قانون\s+(.+?)(?:\s+رقم|\s+لعام)",
        r"مرسوم\s+(.+?)(?:\s+رقم|\s+لعام)",
        r"المادة\s+(\d+)\s+من\s+(.+?)(?:\s+رقم|\s+لعام)",
        r"الفقرة\s+(\d+)\s+من\s+(.+?)(?:\s+رقم|\s+لعام)"
    ]
    
    # Arabic legal keywords
    LEGAL_KEYWORDS = [
        "حق", "واجب", "مسؤولية", "عقوبة", "غرامة", "سجن", "حظر", "منع",
        "إجازة", "ترخيص", "تصريح", "شهادة", "وثيقة", "عقد", "اتفاقية",
        "نظام", "قانون", "مرسوم", "قرار", "لائحة", "تعليمات", "إجراءات",
        "محكمة", "قاضي", "محامي", "شاهد", "دليل", "إثبات", "براءة",
        "ذنب", "جريمة", "جنحة", "مخالفة", "عقاب", "تعزير", "حد",
        "تعويض", "ضرر", "خسارة", "فائدة", "ربح", "مصلحة", "منفعة"
    ]


class DocumentTextExtractor:
    """Handles text extraction from various document formats."""
    
    @staticmethod
    async def extract_from_pdf(file_path: str) -> str:
        """
        Extract text from PDF file with Arabic support.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
            
        Raises:
            ArabicLegalDocumentException: If extraction fails
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
            
        except ImportError:
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text.strip()
            except ImportError:
                raise ArabicLegalDocumentException(
                    "Required PDF processing libraries not installed",
                    document_path=file_path
                )
        except Exception as e:
            raise ArabicLegalDocumentException(
                f"Failed to extract text from PDF: {str(e)}",
                document_path=file_path
            )

    @staticmethod
    async def extract_from_docx(file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
            
        Raises:
            ArabicLegalDocumentException: If extraction fails
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
            
        except ImportError:
            raise ArabicLegalDocumentException(
                "Required DOCX processing library not installed",
                document_path=file_path
            )
        except Exception as e:
            raise ArabicLegalDocumentException(
                f"Failed to extract text from DOCX: {str(e)}",
                document_path=file_path
            )

    @staticmethod
    async def extract_text(file_path: str) -> str:
        """
        Extract text from document based on file extension.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text
            
        Raises:
            ArabicLegalDocumentException: If extraction fails
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return await DocumentTextExtractor.extract_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return await DocumentTextExtractor.extract_from_docx(file_path)
        else:
            raise ArabicLegalDocumentException(
                f"Unsupported file format: {file_extension}",
                document_path=file_path
            )


class LawSourceDetector:
    """Handles detection and extraction of law source metadata."""
    
    @staticmethod
    def detect_law_source(text: str) -> Dict[str, Any]:
        """
        Detect law source information from Arabic text.
        
        Args:
            text: Arabic legal text
            
        Returns:
            Dictionary containing detected law source metadata
        """
        try:
            detected_info = {
                "name": "وثيقة قانونية",
                "type": "law",
                "jurisdiction": "المملكة العربية السعودية",
                "issuing_authority": None,
                "issue_date": None,
                "last_update": None,
                "description": None,
                "source_url": None
            }

            # Extract law name
            for pattern in ArabicLegalPatterns.LAW_NAME_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    detected_info["name"] = match.group(1).strip()
                    break

            # Extract law type
            for pattern, law_type in ArabicLegalPatterns.LAW_TYPE_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_info["type"] = law_type
                    break

            # Extract issuing authority
            for pattern in ArabicLegalPatterns.ISSUING_AUTHORITY_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    detected_info["issuing_authority"] = match.group(1).strip()
                    break

            # Extract issue date
            for pattern in ArabicLegalPatterns.DATE_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    year = int(match.group(1))
                    detected_info["issue_date"] = f"{year}-01-01"
                    break

            # Extract description (first few sentences)
            sentences = re.split(r'[.!?]', text[:500])
            if sentences:
                detected_info["description"] = sentences[0].strip()

            return detected_info

        except Exception as e:
            logger.error(f"Failed to detect law source from text: {str(e)}")
            return {
                "name": "وثيقة قانونية",
                "type": "law",
                "jurisdiction": "المملكة العربية السعودية"
            }

    @staticmethod
    def merge_law_source_details(
        detected: Dict[str, Any], 
        provided: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Merge detected law source details with provided ones.
        
        Args:
            detected: Detected law source details
            provided: Provided law source details
            
        Returns:
            Merged law source details
        """
        if not provided:
            return detected
        
        # Merge provided details with detected ones (provided takes precedence)
        merged = detected.copy()
        for key, value in provided.items():
            if value is not None:
                merged[key] = value
        
        return merged


class ArticleExtractor:
    """Handles extraction of articles from Arabic legal text."""
    
    # Arabic ordinal number mapping
    ARABIC_ORDINALS = {
        "الأولى": "1", "الثانية": "2", "الثالثة": "3", "الرابعة": "4", "الخامسة": "5",
        "السادسة": "6", "السابعة": "7", "الثامنة": "8", "التاسعة": "9", "العاشرة": "10",
        "الحادية عشرة": "11", "الثانية عشرة": "12", "الثالثة عشرة": "13", "الرابعة عشرة": "14",
        "الخامسة عشرة": "15", "السادسة عشرة": "16", "السابعة عشرة": "17", "الثامنة عشرة": "18",
        "التاسعة عشرة": "19", "العشرون": "20", "الحادية والعشرون": "21", "الثانية والعشرون": "22",
        "الثالثة والعشرون": "23", "الرابعة والعشرون": "24", "الخامسة والعشرون": "25",
        "السادسة والعشرون": "26", "السابعة والعشرون": "27", "الثامنة والعشرون": "28",
        "التاسعة والعشرون": "29", "الثلاثون": "30", "الحادية والثلاثون": "31",
        "الثانية والثلاثون": "32", "الثالثة والثلاثون": "33", "الرابعة والثلاثون": "34",
        "الخامسة والثلاثون": "35", "السادسة والثلاثون": "36", "السابعة والثلاثون": "37",
        "الثامنة والثلاثون": "38", "التاسعة والثلاثون": "39", "الأربعون": "40",
        "الحادية والأربعون": "41", "الثانية والأربعون": "42", "الثالثة والأربعون": "43",
        "الرابعة والأربعون": "44", "الخامسة والأربعون": "45", "السادسة والأربعون": "46",
        "السابعة والأربعون": "47", "الثامنة والأربعون": "48", "التاسعة والأربعون": "49",
        "الخمسون": "50", "الحادية والخمسون": "51", "الثانية والخمسون": "52",
        "الثالثة والخمسون": "53", "الرابعة والخمسون": "54", "الخامسة والخمسون": "55",
        "السادسة والخمسون": "56", "السابعة والخمسون": "57", "الثامنة والخمسون": "58",
        "التاسعة والخمسون": "59", "الستون": "60", "الحادية والستون": "61",
        "الثانية والستون": "62", "الثالثة والستون": "63", "الرابعة والستون": "64",
        "الخامسة والستون": "65", "السادسة والستون": "66", "السابعة والستون": "67",
        "الثامنة والستون": "68", "التاسعة والستون": "69", "السبعون": "70",
        "الحادية والسبعون": "71", "الثانية والسبعون": "72", "الثالثة والسبعون": "73",
        "الرابعة والسبعون": "74", "الخامسة والسبعون": "75", "السادسة والسبعون": "76",
        "السابعة والسبعون": "77", "الثامنة والسبعون": "78", "التاسعة والسبعون": "79",
        "الثمانون": "80", "الحادية والثمانون": "81", "الثانية والثمانون": "82",
        "الثالثة والثمانون": "83", "الرابعة والثمانون": "84", "الخامسة والثمانون": "85",
        "السادسة والثمانون": "86", "السابعة والثمانون": "87", "الثامنة والثمانون": "88",
        "التاسعة والثمانون": "89", "التسعون": "90", "الحادية والتسعون": "91",
        "الثانية والتسعون": "92", "الثالثة والتسعون": "93", "الرابعة والتسعون": "94",
        "الخامسة والتسعون": "95", "السادسة والتسعون": "96", "السابعة والتسعون": "97",
        "الثامنة والتسعون": "98", "التاسعة والتسعون": "99", "المائة": "100",
        "الحادية بعد المائة": "101", "الثانية بعد المائة": "102", "الثالثة بعد المائة": "103",
        "الرابعة بعد المائة": "104", "الخامسة بعد المائة": "105", "السادسة بعد المائة": "106",
        "السابعة بعد المائة": "107", "الثامنة بعد المائة": "108", "التاسعة بعد المائة": "109",
        "المائتان": "200", "الحادية بعد المائتين": "201", "الثانية بعد المائتين": "202",
        "الثالثة بعد المائتين": "203", "الرابعة بعد المائتين": "204", "الخامسة بعد المائتين": "205",
        "السادسة بعد المائتين": "206", "السابعة بعد المائتين": "207", "الثامنة بعد المائتين": "208",
        "التاسعة بعد المائتين": "209"
    }
    
    @staticmethod
    def extract_articles(text: str) -> List[Dict[str, Any]]:
        """
        Extract articles from Arabic legal text.
        
        Args:
            text: Arabic legal text
            
        Returns:
            List of extracted articles
        """
        try:
            articles = []
            
            # First, try to find articles with Arabic ordinal numbers
            ordinal_pattern = r"المادة\s+([^:]+?)[:\.]?\s*(.*?)(?=المادة\s+[^:]+?[:\.]|$)"
            matches = re.finditer(ordinal_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                article_ordinal = match.group(1).strip()
                content = match.group(2).strip()
                
                if len(content) > 10:  # Only include substantial content
                    # Convert Arabic ordinal to number
                    article_number = ArticleExtractor.ARABIC_ORDINALS.get(article_ordinal, article_ordinal)
                    
                    # Clean up content using Arabic text processor
                    content = ArabicTextProcessor.normalize_arabic_text(content)
                    
                    # Extract keywords and references
                    keywords = KeywordExtractor.extract_keywords(content)
                    references = ReferenceExtractor.extract_references(content)
                    
                    articles.append({
                        "article_number": f"المادة {article_number}",
                        "title": None,
                        "content": content,
                        "keywords": keywords,
                        "related_references": references
                    })
            
            # If no articles found with ordinal pattern, try numeric patterns
            if not articles:
                for pattern in ArabicLegalPatterns.ARTICLE_PATTERNS[1:]:  # Skip the complex ordinal pattern
                    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        article_number = match.group(1)
                        content = match.group(2).strip()
                        
                        if len(content) > 10:  # Only include substantial content
                            # Clean up content using Arabic text processor
                            content = ArabicTextProcessor.normalize_arabic_text(content)
                            
                            # Extract keywords and references
                            keywords = KeywordExtractor.extract_keywords(content)
                            references = ReferenceExtractor.extract_references(content)
                            
                            articles.append({
                                "article_number": f"المادة {article_number}",
                                "title": None,
                                "content": content,
                                "keywords": keywords,
                                "related_references": references
                            })

            # Sort articles by number
            def get_sort_key(article):
                article_num = article["article_number"]
                # Extract number from "المادة X" format
                num_match = re.search(r'المادة\s+(\d+)', article_num)
                if num_match:
                    return int(num_match.group(1))
                return 0
            
            articles.sort(key=get_sort_key)
            
            return articles

        except Exception as e:
            logger.error(f"Failed to extract articles from text: {str(e)}")
            return []


class KeywordExtractor:
    """Handles extraction of keywords from Arabic legal text."""
    
    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from Arabic article content.
        
        Args:
            content: Article content
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        try:
            keywords = []
            content_lower = content.lower()
            
            # Add legal keywords that appear in content
            for keyword in ArabicLegalPatterns.LEGAL_KEYWORDS:
                if keyword in content_lower:
                    keywords.append(keyword)
            
            # Extract unique words using Arabic text processor
            arabic_keywords = ArabicTextProcessor.extract_arabic_keywords(content, max_keywords)
            for keyword in arabic_keywords:
                if keyword not in keywords:
                    keywords.append(keyword)
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {str(e)}")
            return []


class ReferenceExtractor:
    """Handles extraction of law references from Arabic legal text."""
    
    @staticmethod
    def extract_references(content: str) -> List[str]:
        """
        Extract law references from article content.
        
        Args:
            content: Article content
            
        Returns:
            List of extracted references
        """
        try:
            references = []
            
            for pattern in ArabicLegalPatterns.REFERENCE_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    reference = match.group(0).strip()
                    if reference not in references:
                        references.append(reference)
            
            return references
            
        except Exception as e:
            logger.error(f"Failed to extract references: {str(e)}")
            return []


class DocumentProcessor:
    """Main processor that orchestrates the Arabic legal document processing pipeline."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.text_extractor = DocumentTextExtractor()
        self.law_detector = LawSourceDetector()
        self.article_extractor = ArticleExtractor()
    
    async def process_document(
        self,
        file_path: str,
        law_source_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an Arabic legal document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            law_source_details: Optional law source details
            
        Returns:
            Dictionary containing processed data
            
        Raises:
            ArabicLegalDocumentException: If processing fails
        """
        try:
            # Step 1: Extract text
            text = await self.text_extractor.extract_text(file_path)
            if not text:
                raise ArabicLegalDocumentException(
                    "No text extracted from document",
                    document_path=file_path
                )

            # Step 2: Detect law source
            detected_law_source = self.law_detector.detect_law_source(text)
            law_source = self.law_detector.merge_law_source_details(
                detected_law_source, law_source_details
            )

            # Step 3: Extract articles
            articles = self.article_extractor.extract_articles(text)

            return {
                "law_source": law_source,
                "articles": articles,
                "statistics": {
                    "total_articles": len(articles),
                    "total_characters": sum(len(article["content"]) for article in articles),
                    "processing_time": datetime.now().isoformat(),
                    "file_path": file_path
                }
            }

        except ArabicLegalDocumentException:
            raise
        except Exception as e:
            raise ArabicLegalDocumentException(
                f"Failed to process document: {str(e)}",
                document_path=file_path
            )

    async def process_multiple_documents(
        self,
        file_paths: List[str],
        law_source_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple Arabic legal documents.
        
        Args:
            file_paths: List of file paths
            law_source_details: Optional law source details
            
        Returns:
            Dictionary containing processing results
        """
        results = []
        successful_count = 0
        error_count = 0
        
        for file_path in file_paths:
            try:
                result = await self.process_document(file_path, law_source_details)
                results.append({
                    "file_path": file_path,
                    "success": True,
                    "data": result
                })
                successful_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "results": results,
            "statistics": {
                "total_files": len(file_paths),
                "successful": successful_count,
                "failed": error_count
            }
        }

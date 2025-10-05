"""
Hierarchical Legal Document Structure Processor

This module implements the complete workflow for extracting hierarchical structure
(Chapters → Sections → Articles) from legal documents with maximum accuracy.
"""

import re
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..models.legal_knowledge import (
    LawSource, LawBranch, LawChapter, LawArticle,
    KnowledgeDocument, KnowledgeChunk
)
from ..schemas.legal_knowledge import (
    DocumentStructure, ChapterStructure, SectionStructure, ArticleStructure,
    ProcessingReport, HierarchicalDocumentResponse, DocumentStructureElement
)

logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Types of document elements"""
    CHAPTER = "chapter"
    SECTION = "section"
    ARTICLE = "article"
    SUB_ARTICLE = "sub_article"
    CONTENT = "content"
    IGNORE = "ignore"


@dataclass
class LineAnalysis:
    """Result of line-by-line analysis"""
    line_number: int
    content: str
    element_type: ElementType
    confidence: float
    metadata: Dict[str, Any]
    warnings: List[str]
    errors: List[str]


class ArabicLegalPatternRecognizer:
    """Recognizes Arabic legal document patterns"""
    
    def __init__(self):
        # Arabic legal patterns - updated to match actual text format
        self.chapter_patterns = [
            r'ﺍﻟﺒﺎﺏ ﺍﻷﻭﻝ',  # First chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ', # Second chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻟﺚ', # Third chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺮﺍﺑﻊ', # Fourth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺨﺎﻣﺲ', # Fifth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺩﺱ', # Sixth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺑﻊ', # Seventh chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻣﻦ', # Eighth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺘﺎﺳﻊ', # Ninth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﻌﺎﺷﺮ', # Tenth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺤﺎﺩﻱ ﻋﺸﺮ', # Eleventh chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ ﻋﺸﺮ', # Twelfth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻟﺚ ﻋﺸﺮ', # Thirteenth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺮﺍﺑﻊ ﻋﺸﺮ', # Fourteenth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺨﺎﻣﺲ ﻋﺸﺮ', # Fifteenth chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺩﺱ ﻋﺸﺮ', # Sixteenth chapter
            # Original patterns as fallback
            r'الباب\s+(?:ال)?(?:أول|ثاني|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر)',
            r'الباب\s+(\d+)'
        ]
        
        self.section_patterns = [
            r'ﺍﻟﻔﺼﻞ ﺍﻷﻭﻝ',  # First section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺜﺎﻧﻲ', # Second section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺜﺎﻟﺚ', # Third section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺮﺍﺑﻊ', # Fourth section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺨﺎﻣﺲ', # Fifth section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺴﺎﺩﺱ', # Sixth section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺴﺎﺑﻊ', # Seventh section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺜﺎﻣﻦ', # Eighth section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﺘﺎﺳﻊ', # Ninth section
            r'ﺍﻟﻔﺼﻞ ﺍﻟﻌﺎﺷﺮ', # Tenth section
            # Original patterns as fallback
            r'(?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً|سابعاً|ثامناً|تاسعاً|عاشراً)',
            r'الفصل\s+(?:ال)?(?:أول|ثاني|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر)'
        ]
        
        self.article_patterns = [
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ', # First article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ', # Second article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻟﺜﺔ', # Third article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺮﺍﺑﻌﺔ', # Fourth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺨﺎﻣﺴﺔ', # Fifth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺩﺳﺔ', # Sixth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺑﻌﺔ', # Seventh article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻣﻨﺔ', # Eighth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺘﺎﺳﻌﺔ', # Ninth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﻌﺎﺷﺮﺓ', # Tenth article
            # Pattern for numbered articles (like "المادة الخامسة والعشرون")
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺨﺎﻣﺴﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # Twenty-fifth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # Twenty-second article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻟﺜﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # Twenty-third article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺮﺍﺑﻌﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # Twenty-fourth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ ﻋﺸﺮﺓ', # Twelfth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻟﺜﺔ ﻋﺸﺮﺓ', # Thirteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺮﺍﺑﻌﺔ ﻋﺸﺮﺓ', # Fourteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺨﺎﻣﺴﺔ ﻋﺸﺮﺓ', # Fifteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺩﺳﺔ ﻋﺸﺮﺓ', # Sixteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺑﻌﺔ ﻋﺸﺮﺓ', # Seventeenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻣﻨﺔ ﻋﺸﺮﺓ', # Eighteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺘﺎﺳﻌﺔ ﻋﺸﺮﺓ', # Nineteenth article
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﻌﺎﺷﺮﺓ', # Twentieth article
            # Original patterns as fallback
            r'المادة\s+(\d+(?:/\d+)?)',
            r'مادة\s+(\d+(?:/\d+)?)',
            r'م\.\s*(\d+(?:/\d+)?)'
        ]
        
        self.sub_article_patterns = [
            r'(\d+)\s*[-–—]\s*',
            r'([أ-ي])\s*[-–—]\s*',
            r'(\d+)\s*\)\s*',
            r'([أ-ي])\s*\)\s*',
            r'(\d+)\.\s*',
            r'([أ-ي])\.\s*'
        ]
        
        # Compile patterns for efficiency
        self.chapter_regexes = [re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in self.chapter_patterns]
        self.section_regexes = [re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in self.section_patterns]
        self.article_regexes = [re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in self.article_patterns]
        self.sub_article_regexes = [re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in self.sub_article_patterns]
        
        # Arabic number mappings
        self.arabic_to_english = {
            'أول': '1', 'ثاني': '2', 'ثالث': '3', 'رابع': '4', 'خامس': '5',
            'سادس': '6', 'سابع': '7', 'ثامن': '8', 'تاسع': '9', 'عاشر': '10',
            'حادي عشر': '11', 'ثاني عشر': '12', 'ثالث عشر': '13', 'رابع عشر': '14',
            'خامس عشر': '15', 'سادس عشر': '16', 'سابع عشر': '17', 'ثامن عشر': '18',
            'تاسع عشر': '19', 'عشرون': '20', 'واحد وعشرون': '21', 'اثنان وعشرون': '22',
            'ثلاثة وعشرون': '23', 'أربعة وعشرون': '24', 'خمسة وعشرون': '25',
            'ستة وعشرون': '26', 'سبعة وعشرون': '27', 'ثمانية وعشرون': '28',
            'تسعة وعشرون': '29', 'ثلاثون': '30',
            'أولى': '1', 'ثانية': '2', 'ثالثة': '3', 'رابعة': '4', 'خامسة': '5',
            'سادسة': '6', 'سابعة': '7', 'ثامنة': '8', 'تاسعة': '9', 'عاشرة': '10',
            'الحادية': '11', 'الثانية': '12', 'الثالثة': '13', 'الرابعة': '14',
            'الخامسة': '15', 'السادسة': '16', 'السابعة': '17', 'الثامنة': '18',
            'التاسعة': '19', 'العاشرة': '20'
        }
    
    def normalize_arabic_number(self, text: str) -> str:
        """Convert Arabic numbers to English digits"""
        for arabic, english in self.arabic_to_english.items():
            text = text.replace(arabic, english)
        return text
    
    def analyze_line(self, line: str, line_number: int, context: Dict[str, Any] = None) -> LineAnalysis:
        """Analyze a single line to determine its type and extract metadata"""
        line = line.strip()
        if not line:
            return LineAnalysis(
                line_number=line_number,
                content=line,
                element_type=ElementType.IGNORE,
                confidence=1.0,
                metadata={},
                warnings=[],
                errors=[]
            )
        
        # Check for chapter patterns
        for i, regex in enumerate(self.chapter_regexes):
            match = regex.search(line)
            if match:
                number = match.group(1) if match.groups() else None
                if not number:
                    # Extract Arabic number from the match
                    number = self.normalize_arabic_number(match.group(0))
                
                return LineAnalysis(
                    line_number=line_number,
                    content=line,
                    element_type=ElementType.CHAPTER,
                    confidence=0.95 if i < 2 else 0.85,  # Higher confidence for exact matches
                    metadata={
                        'number': number,
                        'title': line.replace(match.group(0), '').strip(),
                        'pattern_index': i,
                        'match_text': match.group(0)
                    },
                    warnings=[],
                    errors=[]
                )
        
        # Check for section patterns
        for i, regex in enumerate(self.section_regexes):
            match = regex.search(line)
            if match:
                number = match.group(1) if match.groups() else None
                if not number:
                    number = self.normalize_arabic_number(match.group(0))
                
                return LineAnalysis(
                    line_number=line_number,
                    content=line,
                    element_type=ElementType.SECTION,
                    confidence=0.90 if i < 3 else 0.80,
                    metadata={
                        'number': number,
                        'title': line.replace(match.group(0), '').strip(),
                        'pattern_index': i,
                        'match_text': match.group(0)
                    },
                    warnings=[],
                    errors=[]
                )
        
        # Check for article patterns
        for i, regex in enumerate(self.article_regexes):
            match = regex.search(line)
            if match:
                number = match.group(1) if match.groups() else None
                if not number:
                    number = self.normalize_arabic_number(match.group(0))
                
                return LineAnalysis(
                    line_number=line_number,
                    content=line,
                    element_type=ElementType.ARTICLE,
                    confidence=0.95 if i < 2 else 0.85,
                    metadata={
                        'number': number,
                        'title': line.replace(match.group(0), '').strip(),
                        'pattern_index': i,
                        'match_text': match.group(0)
                    },
                    warnings=[],
                    errors=[]
                )
        
        # Check for sub-article patterns
        for i, regex in enumerate(self.sub_article_regexes):
            match = regex.search(line)
            if match:
                number = match.group(1)
                return LineAnalysis(
                    line_number=line_number,
                    content=line,
                    element_type=ElementType.SUB_ARTICLE,
                    confidence=0.80,
                    metadata={
                        'number': number,
                        'title': line.replace(match.group(0), '').strip(),
                        'pattern_index': i,
                        'match_text': match.group(0)
                    },
                    warnings=[],
                    errors=[]
                )
        
        # Default to content
        return LineAnalysis(
            line_number=line_number,
            content=line,
            element_type=ElementType.CONTENT,
            confidence=0.70,
            metadata={},
            warnings=[],
            errors=[]
        )


class HierarchicalDocumentProcessor:
    """Main processor for hierarchical document structure extraction"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pattern_recognizer = ArabicLegalPatternRecognizer()
        self.processing_start_time = None
        self.processing_report = ProcessingReport(
            warnings=[],
            errors=[],
            suggestions=[],
            processing_time=0.0,
            text_length=0,
            pages_processed=0
        )
    
    async def process_document(
        self,
        file_path: str,
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a legal document and extract hierarchical structure"""
        self.processing_start_time = time.time()
        
        try:
            # Phase 1: Document Preparation
            text = await self._extract_text_from_file(file_path)
            self.processing_report.text_length = len(text)
            
            # Phase 2: Structure Analysis
            line_analyses = await self._analyze_document_structure(text)
            
            # Phase 3: Hierarchy Reconstruction
            document_structure = await self._reconstruct_hierarchy(line_analyses)
            
            # Phase 4: Quality Assurance
            await self._validate_structure(document_structure)
            
            # Phase 5: Data Persistence
            law_source = await self._persist_to_database(
                document_structure, law_source_details, uploaded_by
            )
            
            # Calculate processing time
            self.processing_report.processing_time = time.time() - self.processing_start_time
            
            return {
                "success": True,
                "message": "Document processed successfully with hierarchical structure extracted",
                "data": {
                    "law_source": law_source,
                    "structure": document_structure,
                    "processing_report": self.processing_report
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process document: {str(e)}")
            self.processing_report.errors.append(f"Processing failed: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process document: {str(e)}",
                "data": None
            }
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or Word document"""
        try:
            # Check file extension to determine processing method
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension in ['pdf']:
                # Use the enhanced Arabic PDF processor for PDFs
                from .enhanced_arabic_pdf_processor import EnhancedArabicPDFProcessor
                
                processor = EnhancedArabicPDFProcessor()
                text, method = processor.extract_pdf_text(file_path, language='ar')
                
                if not text or not text.strip():
                    raise Exception("No text could be extracted from the PDF")
                
                # Process the extracted text for better quality
                processed_result = processor.process_extracted_text(text)
                raw_text = processed_result.get('text', text)
                
                # Fix Arabic text direction (reverse characters in each line)
                corrected_text = self._fix_arabic_text_direction(raw_text)
                return corrected_text
                
            elif file_extension in ['docx', 'doc']:
                # Use the enhanced document processor for Word documents
                from .enhanced_document_processor import EnhancedDocumentProcessor
                
                processor = EnhancedDocumentProcessor()
                text = await processor.extract_text(file_path, language='ar')
                
                if not text or not text.strip():
                    raise Exception("No text could be extracted from the Word document")
                
                # Fix Arabic text direction
                corrected_text = self._fix_arabic_text_direction(text)
                return corrected_text
                
            else:
                raise Exception(f"Unsupported file type: {file_extension}. Supported formats: PDF, DOCX, DOC")
                
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise Exception(f"Failed to extract text from file: {str(e)}")
    
    def _fix_arabic_text_direction(self, text: str) -> str:
        """Fix Arabic text direction using proper bidirectional text processing"""
        try:
            # Import Arabic text processing libraries
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
            except ImportError:
                logger.warning("Arabic text processing libraries not available, using simple reversal")
                return self._simple_reverse_text(text)
            
            lines = text.split('\n')
            corrected_lines = []
            
            for line in lines:
                if line.strip():
                    # Reshape Arabic text
                    reshaped_text = arabic_reshaper.reshape(line)
                    # Apply bidirectional algorithm
                    corrected_line = get_display(reshaped_text)
                    corrected_lines.append(corrected_line)
                else:
                    corrected_lines.append(line)
            
            return '\n'.join(corrected_lines)
            
        except Exception as e:
            logger.warning(f"Failed to fix Arabic text direction: {str(e)}, using simple reversal")
            return self._simple_reverse_text(text)
    
    def _simple_reverse_text(self, text: str) -> str:
        """Simple text reversal as fallback"""
        try:
            lines = text.split('\n')
            corrected_lines = []
            
            for line in lines:
                # Reverse the line to fix Arabic text direction
                corrected_line = line[::-1]
                corrected_lines.append(corrected_line)
            
            return '\n'.join(corrected_lines)
            
        except Exception as e:
            logger.warning(f"Failed to reverse text: {str(e)}")
            return text
    
    def _detect_table_of_contents_sections(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Detect table of contents sections in the document.
        
        Returns list of (start_line, end_line) tuples for TOC sections.
        """
        toc_sections = []
        current_toc_start = None
        
        # Patterns that indicate table of contents
        toc_indicators = [
            r'الفهرس',
            r'جدول المحتويات',
            r'المحتويات',
            r'محتوى الكتاب',
            r'فهرس المحتويات',
            r'index',
            r'table of contents',
            r'contents'
        ]
        
        # Also detect TOC by pattern: chapter/section names followed by page numbers
        # This is common in Arabic legal documents
        toc_pattern_detected = False
        
        # Patterns that indicate end of table of contents
        toc_end_indicators = [
            r'الفصل الأول',
            r'الباب الأول',
            r'المادة الأولى',
            r'بداية النص',
            r'start of text',
            r'beginning of document'
        ]
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check for TOC start indicators
            if current_toc_start is None:
                # Check explicit TOC indicators
                for indicator in toc_indicators:
                    if re.search(indicator, line_clean, re.IGNORECASE):
                        current_toc_start = i + 1  # 1-based line numbering
                        logger.info(f"Found TOC start at line {current_toc_start}: {line[:50]}...")
                        break
                
                # Also detect TOC by pattern: lines ending with page numbers
                # Pattern: "Chapter/Section Name ... 31" or "الباب الأول ... 31"
                if not current_toc_start:
                    # Look for lines that contain chapter/section patterns followed by page numbers
                    page_number_at_end = r'\s+\d+\s*$'
                    if re.search(page_number_at_end, line.strip()):
                        # Check if this line contains chapter/section keywords
                        chapter_section_keywords = [r'الباب', r'الفصل', r'المادة', r'أولاً', r'ثانياً', r'ﺍﻟﺒﺎﺏ', r'ﺍﻟﻔﺼﻞ', r'ﺍﻟﻤﺎﺩﺓ']
                        for keyword in chapter_section_keywords:
                            if re.search(keyword, line, re.IGNORECASE):
                                current_toc_start = i + 1
                                logger.info(f"Found TOC by pattern at line {current_toc_start}: {line[:50]}...")
                                break
            
            # Check for TOC end indicators or patterns that suggest end of TOC
            elif current_toc_start is not None:
                should_end_toc = False
                
                # Check explicit end indicators
                for indicator in toc_end_indicators:
                    if re.search(indicator, line_clean, re.IGNORECASE):
                        should_end_toc = True
                        break
                
                # Check for patterns that suggest we're now in the main document
                # Look for page numbers followed by chapter/section headers
                page_number_pattern = r'^\s*\d+\s*$'
                if re.match(page_number_pattern, line_clean):
                    # Check if next few lines contain chapter patterns
                    next_lines = lines[i+1:i+4]
                    for next_line in next_lines:
                        if self.pattern_recognizer.analyze_line(next_line, i+2).element_type == ElementType.CHAPTER:
                            should_end_toc = True
                            break
                
                # Check for consecutive lines with page numbers (typical TOC pattern)
                if i > 0 and re.match(page_number_pattern, line_clean):
                    prev_line = lines[i-1].strip().lower()
                    # If previous line also has page number pattern, likely still in TOC
                    if not re.match(page_number_pattern, prev_line):
                        # Check if this line is followed by structural elements
                        if i < len(lines) - 2:
                            next_analysis = self.pattern_recognizer.analyze_line(lines[i+1], i+2)
                            if next_analysis.element_type in [ElementType.CHAPTER, ElementType.SECTION]:
                                should_end_toc = True
                
                # Additional check: if we encounter a line that starts with chapter/section patterns
                # but doesn't end with page numbers, we're likely out of TOC
                chapter_start_patterns = [r'ﺍﻟﺒﺎﺏ ﺍﻷﻭﻝ', r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ', r'ﺍﻟﻔﺼﻞ ﺍﻷﻭﻝ', r'ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ']
                for pattern in chapter_start_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if this line doesn't end with page number
                        if not re.search(page_number_at_end, line.strip()):
                            should_end_toc = True
                            break
                
                if should_end_toc:
                    toc_sections.append((current_toc_start, i))
                    logger.info(f"Found TOC end at line {i}: {line[:50]}...")
                    current_toc_start = None
        
        # If we found a TOC start but no end, assume it continues to end of document
        if current_toc_start is not None:
            toc_sections.append((current_toc_start, len(lines)))
            logger.info(f"TOC section continues to end of document from line {current_toc_start}")
        
        return toc_sections
    
    def _is_in_table_of_contents(self, line_number: int, toc_sections: List[Tuple[int, int]]) -> bool:
        """Check if a line number is within any table of contents section."""
        for start_line, end_line in toc_sections:
            if start_line <= line_number <= end_line:
                return True
        return False
    
    async def _analyze_document_structure(self, text: str) -> List[LineAnalysis]:
        """Analyze document structure line by line"""
        lines = text.split('\n')
        line_analyses = []
        
        # Detect table of contents sections to exclude
        toc_sections = self._detect_table_of_contents_sections(lines)
        
        for i, line in enumerate(lines, 1):
            # Skip lines that are in table of contents sections
            if self._is_in_table_of_contents(i, toc_sections):
                analysis = LineAnalysis(
                    line_number=i,
                    content=line,
                    element_type=ElementType.IGNORE,
                    confidence=1.0,
                    metadata={'reason': 'table_of_contents'},
                    warnings=[],
                    errors=[]
                )
            else:
                analysis = self.pattern_recognizer.analyze_line(line, i)
            
            line_analyses.append(analysis)
        
        return line_analyses
    
    async def _reconstruct_hierarchy(self, line_analyses: List[LineAnalysis]) -> DocumentStructure:
        """Reconstruct hierarchical structure from line analyses"""
        chapters = []
        orphaned_articles = []
        current_chapter = None
        current_section = None
        current_article = None
        
        for analysis in line_analyses:
            if analysis.element_type == ElementType.CHAPTER:
                # Save previous chapter if exists
                if current_chapter:
                    chapters.append(current_chapter)
                
                # Create new chapter
                chapter_title = analysis.metadata.get('title', '').strip()
                if not chapter_title:
                    chapter_title = f"Chapter {analysis.metadata.get('number', len(chapters) + 1)}"
                
                current_chapter = ChapterStructure(
                    number=analysis.metadata.get('number', ''),
                    title=chapter_title,
                    confidence=analysis.confidence,
                    warnings=analysis.warnings,
                    errors=analysis.errors,
                    sections=[],
                    articles=[],
                    order_index=len(chapters)
                )
                current_section = None
                current_article = None
                
            elif analysis.element_type == ElementType.SECTION and current_chapter:
                # Create new section
                section_title = analysis.metadata.get('title', '').strip()
                if not section_title:
                    section_title = f"Section {analysis.metadata.get('number', len(current_chapter.sections) + 1)}"
                
                current_section = SectionStructure(
                    number=analysis.metadata.get('number', ''),
                    title=section_title,
                    confidence=analysis.confidence,
                    warnings=analysis.warnings,
                    errors=analysis.errors,
                    articles=[],
                    order_index=len(current_chapter.sections)
                )
                current_chapter.sections.append(current_section)
                current_article = None
                
            elif analysis.element_type == ElementType.ARTICLE:
                # Create new article
                article_title = analysis.metadata.get('title', '').strip()
                if not article_title:
                    article_title = f"Article {analysis.metadata.get('number', '')}"
                
                article = ArticleStructure(
                    number=analysis.metadata.get('number', ''),
                    title=article_title,
                    content=analysis.content,
                    confidence=analysis.confidence,
                    warnings=analysis.warnings,
                    errors=analysis.errors,
                    order_index=0
                )
                
                if current_section:
                    # Article belongs to current section
                    article.order_index = len(current_section.articles)
                    current_section.articles.append(article)
                elif current_chapter:
                    # Article belongs to current chapter (not in any section)
                    article.order_index = len(current_chapter.articles)
                    current_chapter.articles.append(article)
                else:
                    # Orphaned article
                    article.order_index = len(orphaned_articles)
                    orphaned_articles.append(article)
                
                current_article = article
                
            elif analysis.element_type == ElementType.SUB_ARTICLE and current_article:
                # Add sub-article to current article
                sub_article_title = analysis.metadata.get('title', '').strip()
                if not sub_article_title:
                    sub_article_title = f"Sub-article {analysis.metadata.get('number', '')}"
                
                sub_article = ArticleStructure(
                    number=analysis.metadata.get('number', ''),
                    title=sub_article_title,
                    content=analysis.content,
                    confidence=analysis.confidence,
                    warnings=analysis.warnings,
                    errors=analysis.errors,
                    order_index=len(current_article.sub_articles or [])
                )
                
                if not current_article.sub_articles:
                    current_article.sub_articles = []
                current_article.sub_articles.append(sub_article)
                
            elif analysis.element_type == ElementType.CONTENT and current_article:
                # Add content to current article
                if current_article.content:
                    current_article.content += " " + analysis.content
                else:
                    current_article.content = analysis.content
        
        # Add final chapter if exists
        if current_chapter:
            chapters.append(current_chapter)
        
        # Calculate statistics
        total_chapters = len(chapters)
        total_sections = sum(len(chapter.sections) for chapter in chapters)
        total_articles = (
            sum(len(chapter.articles) for chapter in chapters) +
            sum(len(section.articles) for chapter in chapters for section in chapter.sections) +
            len(orphaned_articles)
        )
        
        # Calculate overall confidence
        all_elements = []
        for chapter in chapters:
            all_elements.append(chapter)
            all_elements.extend(chapter.sections)
            all_elements.extend(chapter.articles)
            for section in chapter.sections:
                all_elements.extend(section.articles)
        all_elements.extend(orphaned_articles)
        
        overall_confidence = (
            sum(element.confidence for element in all_elements) / len(all_elements)
            if all_elements else 0.0
        )
        
        return DocumentStructure(
            chapters=chapters,
            orphaned_articles=orphaned_articles,
            total_chapters=total_chapters,
            total_sections=total_sections,
            total_articles=total_articles,
            structure_confidence=overall_confidence
        )
    
    async def _validate_structure(self, structure: DocumentStructure) -> None:
        """Validate the extracted structure and add warnings/errors"""
        warnings = []
        errors = []
        
        # Check for missing elements
        if structure.total_chapters == 0:
            warnings.append("No chapters detected in document")
        
        if structure.total_sections == 0 and structure.total_articles > 0:
            warnings.append("Articles found but no sections detected")
        
        # Check numbering continuity
        for chapter in structure.chapters:
            if chapter.number and not chapter.number.isdigit():
                warnings.append(f"Chapter {chapter.number} has non-numeric numbering")
            
            for section in chapter.sections:
                if section.number and not section.number.isdigit():
                    warnings.append(f"Section {section.number} in chapter {chapter.number} has non-numeric numbering")
        
        # Check for orphaned articles
        if structure.orphaned_articles:
            warnings.append(f"{len(structure.orphaned_articles)} articles found outside any chapter/section")
        
        # Check confidence scores
        low_confidence_elements = []
        for chapter in structure.chapters:
            if chapter.confidence < 0.7:
                low_confidence_elements.append(f"Chapter {chapter.number}")
            for section in chapter.sections:
                if section.confidence < 0.7:
                    low_confidence_elements.append(f"Section {section.number} in chapter {chapter.number}")
        
        if low_confidence_elements:
            warnings.append(f"Low confidence elements detected: {', '.join(low_confidence_elements)}")
        
        # Add suggestions
        suggestions = []
        if structure.structure_confidence < 0.8:
            suggestions.append("Consider manual review due to low overall confidence")
        if warnings:
            suggestions.append("Review warnings and consider manual correction")
        
        self.processing_report.warnings.extend(warnings)
        self.processing_report.errors.extend(errors)
        self.processing_report.suggestions.extend(suggestions)
    
    async def _persist_to_database(
        self,
        structure: DocumentStructure,
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Persist the extracted structure to database"""
        try:
            # Create law source
            law_source = LawSource(
                name=law_source_details.get('name', 'Extracted Legal Document') if law_source_details else 'Extracted Legal Document',
                type=law_source_details.get('type', 'law') if law_source_details else 'law',
                jurisdiction=law_source_details.get('jurisdiction') if law_source_details else None,
                issuing_authority=law_source_details.get('issuing_authority') if law_source_details else None,
                issue_date=law_source_details.get('issue_date') if law_source_details else None,
                last_update=law_source_details.get('last_update') if law_source_details else None,
                description=law_source_details.get('description') if law_source_details else None,
                source_url=law_source_details.get('source_url') if law_source_details else None,
                upload_file_path=law_source_details.get('upload_file_path') if law_source_details else None
            )
            
            self.db.add(law_source)
            await self.db.flush()  # Get the ID
            
            # Process chapters and their content
            for chapter_structure in structure.chapters:
                # Create chapter (as branch in our schema)
                branch = LawBranch(
                    law_source_id=law_source.id,
                    branch_number=chapter_structure.number,
                    branch_name=chapter_structure.title,
                    description=f"Chapter {chapter_structure.number}",
                    order_index=chapter_structure.order_index
                )
                
                self.db.add(branch)
                await self.db.flush()
                
                # Process sections and articles within this chapter
                for section_structure in chapter_structure.sections:
                    # Create section (as chapter in our schema)
                    chapter = LawChapter(
                        branch_id=branch.id,
                        chapter_number=section_structure.number,
                        chapter_name=section_structure.title,
                        description=f"Section {section_structure.number}",
                        order_index=section_structure.order_index
                    )
                    
                    self.db.add(chapter)
                    await self.db.flush()
                    
                    # Create articles in this section
                    for article_structure in section_structure.articles:
                        article = LawArticle(
                            law_source_id=law_source.id,
                            branch_id=branch.id,
                            chapter_id=chapter.id,
                            article_number=article_structure.number,
                            title=article_structure.title,
                            content=article_structure.content,
                            keywords=[],  # Could be extracted using NLP
                            embedding=None,  # Could be generated using embeddings
                            order_index=article_structure.order_index
                        )
                        
                        self.db.add(article)
                
                # Process direct articles in chapter (not in any section)
                for article_structure in chapter_structure.articles:
                    article = LawArticle(
                        law_source_id=law_source.id,
                        branch_id=branch.id,
                        chapter_id=None,
                        article_number=article_structure.number,
                        title=article_structure.title,
                        content=article_structure.content,
                        keywords=[],
                        embedding=None,
                        order_index=article_structure.order_index
                    )
                    
                    self.db.add(article)
            
            # Process orphaned articles
            for article_structure in structure.orphaned_articles:
                article = LawArticle(
                    law_source_id=law_source.id,
                    branch_id=None,
                    chapter_id=None,
                    article_number=article_structure.number,
                    title=article_structure.title,
                    content=article_structure.content,
                    keywords=[],
                    embedding=None,
                    order_index=article_structure.order_index
                )
                
                self.db.add(article)
            
            await self.db.commit()
            
            return {
                "id": law_source.id,
                "name": law_source.name,
                "type": law_source.type,
                "jurisdiction": law_source.jurisdiction,
                "created_at": law_source.created_at,
                "structure_stats": {
                    "chapters": structure.total_chapters,
                    "sections": structure.total_sections,
                    "articles": structure.total_articles,
                    "confidence": structure.structure_confidence
                }
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to persist structure to database: {str(e)}")
            raise Exception(f"Database persistence failed: {str(e)}")
    
    async def validate_structure(
        self,
        law_source_id: int,
        validate_numbering: bool = True,
        validate_hierarchy: bool = True,
        detect_gaps: bool = True
    ) -> Dict[str, Any]:
        """Validate existing structure in database"""
        try:
            # Query the law source and its hierarchical structure
            law_source_query = select(LawSource).where(LawSource.id == law_source_id)
            law_source_result = await self.db.execute(law_source_query)
            law_source = law_source_result.scalar_one_or_none()
            
            if not law_source:
                return {
                    "success": False,
                    "message": "Law source not found",
                    "data": None
                }
            
            # Query branches (chapters)
            branches_query = select(LawBranch).where(LawBranch.law_source_id == law_source_id).order_by(LawBranch.order_index)
            branches_result = await self.db.execute(branches_query)
            branches = branches_result.scalars().all()
            
            # Query chapters (sections) for each branch
            chapters = []
            for branch in branches:
                chapter_query = select(LawChapter).where(LawChapter.branch_id == branch.id).order_by(LawChapter.order_index)
                chapter_result = await self.db.execute(chapter_query)
                branch_chapters = chapter_result.scalars().all()
                chapters.extend(branch_chapters)
            
            # Query articles
            articles_query = select(LawArticle).where(LawArticle.law_source_id == law_source_id).order_by(LawArticle.order_index)
            articles_result = await self.db.execute(articles_query)
            articles = articles_result.scalars().all()
            
            # Perform validation
            issues = []
            statistics = {
                "total_branches": len(branches),
                "total_chapters": len(chapters),
                "total_articles": len(articles),
                "orphaned_articles": len([a for a in articles if not a.branch_id])
            }
            
            if validate_numbering:
                # Check numbering continuity
                for branch in branches:
                    if branch.branch_number and not branch.branch_number.isdigit():
                        issues.append({
                            "type": "numbering_issue",
                            "level": "branch",
                            "id": branch.id,
                            "message": f"Branch {branch.branch_number} has non-numeric numbering"
                        })
            
            if validate_hierarchy:
                # Check parent-child relationships
                for article in articles:
                    if article.chapter_id:
                        # Article should belong to a branch through its chapter
                        chapter = next((c for c in chapters if c.id == article.chapter_id), None)
                        if chapter and article.branch_id != chapter.branch_id:
                            issues.append({
                                "type": "hierarchy_issue",
                                "level": "article",
                                "id": article.id,
                                "message": f"Article {article.article_number} has inconsistent branch/chapter relationship"
                            })
            
            if detect_gaps:
                # Check for missing elements
                if len(articles) == 0:
                    issues.append({
                        "type": "missing_content",
                        "level": "document",
                        "message": "No articles found in document"
                    })
            
            is_valid = len(issues) == 0
            confidence = 1.0 - (len(issues) * 0.1) if issues else 1.0
            confidence = max(0.0, confidence)
            
            return {
                "success": True,
                "message": "Structure validation completed",
                "data": {
                    "is_valid": is_valid,
                    "confidence": confidence,
                    "issues": issues,
                    "suggestions": [
                        "Review and fix detected issues",
                        "Consider manual correction for complex structures"
                    ] if issues else ["Structure appears to be valid"],
                    "statistics": statistics
                }
            }
            
        except Exception as e:
            logger.error(f"Structure validation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Structure validation failed: {str(e)}",
                "data": None
            }

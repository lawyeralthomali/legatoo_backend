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
        # Arabic legal patterns - ORDERED BY LENGTH (longest first) to prevent partial matches
        # This ensures "الباب الثاني عشر" is matched before "الباب الثاني"
        self.chapter_patterns = [
            # Compound numbers (11-19) - MUST come first
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺤﺎﺩﻱ ﻋﺸﺮ',   # 11th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ ﻋﺸﺮ',    # 12th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻟﺚ ﻋﺸﺮ',    # 13th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺮﺍﺑﻊ ﻋﺸﺮ',     # 14th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺨﺎﻣﺲ ﻋﺸﺮ',    # 15th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺩﺱ ﻋﺸﺮ',    # 16th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺑﻊ ﻋﺸﺮ',    # 17th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻣﻦ ﻋﺸﺮ',    # 18th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺘﺎﺳﻊ ﻋﺸﺮ',    # 19th chapter
            # Simple numbers (1-10)
            r'ﺍﻟﺒﺎﺏ ﺍﻷﻭﻝ',           # 1st chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻧﻲ',          # 2nd chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻟﺚ',          # 3rd chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺮﺍﺑﻊ',          # 4th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺨﺎﻣﺲ',          # 5th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺩﺱ',          # 6th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺴﺎﺑﻊ',          # 7th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺜﺎﻣﻦ',          # 8th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﺘﺎﺳﻊ',          # 9th chapter
            r'ﺍﻟﺒﺎﺏ ﺍﻟﻌﺎﺷﺮ',          # 10th chapter
            # Fallback patterns for non-encoded text
            r'الباب\s+(?:ال)?(?:حادي|ثاني|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع)\s+عشر',  # 11-19
            r'الباب\s+(?:ال)?(?:أول|ثاني|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر)',   # 1-10
            r'الباب\s+(\d+)'  # Numeric fallback
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
            # ★ تحسين: إضافة أنماط متعددة للتعامل مع اختلافات الترميز والحركات ★
            # Compound numbers with "والعشرون" (21-29) - MUST come first
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺤﺎﺩﻳﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 21st
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 22nd
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻟﺜﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 23rd
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺮﺍﺑﻌﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 24th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺨﺎﻣﺴﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 25th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺩﺳﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 26th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺑﻌﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 27th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻣﻨﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 28th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺘﺎﺳﻌﺔ ﻭﺍﻟﻌﺸﺮﻭﻥ', # 29th
            # Compound numbers with "عشرة" (11-19)
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺤﺎﺩﻳﺔ ﻋﺸﺮﺓ', # 11th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻧﻴﺔ ﻋﺸﺮﺓ', # 12th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻟﺜﺔ ﻋﺸﺮﺓ', # 13th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺮﺍﺑﻌﺔ ﻋﺸﺮﺓ', # 14th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺨﺎﻣﺴﺔ ﻋﺸﺮﺓ', # 15th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺩﺳﺔ ﻋﺸﺮﺓ', # 16th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺴﺎﺑﻌﺔ ﻋﺸﺮﺓ', # 17th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺜﺎﻣﻨﺔ ﻋﺸﺮﺓ', # 18th
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻟﺘﺎﺳﻌﺔ ﻋﺸﺮﺓ', # 19th
            # Simple numbers (1-10) - Encoded version
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
            # ★ أنماط بديلة للتعامل مع الفروقات في ترميز PDF ★
            # Simple numbers (1-10) - Normal encoding with variations
            r'المادة\s+الأولى',
            r'المادة\s+الاولى',  # بدون همزة
            r'المادة\s+الثانية',
            r'المادة\s+الثالثة',
            r'المادة\s+الرابعة',
            r'المادة\s+الخامسة',
            r'المادة\s+السادسة',
            r'المادة\s+السابعة',
            r'المادة\s+الثامنة',
            r'المادة\s+التاسعة',
            r'المادة\s+العاشرة',
            # Compound patterns with flexible spacing
            r'المادة\s+(?:ال)?(?:حادية|ثانية|ثالثة|رابعة|خامسة|سادسة|سابعة|ثامنة|تاسعة)\s+عشرة',  # 11-19
            r'المادة\s+(?:ال)?(?:حادية|ثانية|ثالثة|رابعة|خامسة|سادسة|سابعة|ثامنة|تاسعة)\s+والعشرون',  # 21-29
            # Numeric patterns (most flexible)
            r'المادة\s*[:：]\s*(\d+(?:/\d+)?)',  # المادة: 15
            r'المادة\s+(\d+(?:/\d+)?)',          # المادة 15
            r'مادة\s+(\d+(?:/\d+)?)',            # مادة 15
            r'م\s*[.．]\s*(\d+(?:/\d+)?)',       # م. 15
            r'المادة\s+([٠-٩]+)',                 # أرقام عربية
            r'مادة\s+رقم\s+(\d+)'                # مادة رقم 15
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
        
        # ★ خريطة موسعة للأرقام العربية مع تنويعات مختلفة ★
        self.arabic_to_english = {
            # أرقام مذكرة (للأبواب والفصول)
            'أول': '1', 'الأول': '1', 'اول': '1', 'الاول': '1',
            'ثاني': '2', 'الثاني': '2',
            'ثالث': '3', 'الثالث': '3',
            'رابع': '4', 'الرابع': '4',
            'خامس': '5', 'الخامس': '5',
            'سادس': '6', 'السادس': '6',
            'سابع': '7', 'السابع': '7',
            'ثامن': '8', 'الثامن': '8',
            'تاسع': '9', 'التاسع': '9',
            'عاشر': '10', 'العاشر': '10',
            # أرقام مؤنثة (للمواد)
            'أولى': '1', 'الأولى': '1', 'اولى': '1', 'الاولى': '1',
            'ثانية': '2', 'الثانية': '2',
            'ثالثة': '3', 'الثالثة': '3',
            'رابعة': '4', 'الرابعة': '4',
            'خامسة': '5', 'الخامسة': '5',
            'سادسة': '6', 'السادسة': '6',
            'سابعة': '7', 'السابعة': '7',
            'ثامنة': '8', 'الثامنة': '8',
            'تاسعة': '9', 'التاسعة': '9',
            'عاشرة': '10', 'العاشرة': '10',
            # أرقام مركبة (11-19) - مذكرة
            'حادي عشر': '11', 'الحادي عشر': '11',
            'ثاني عشر': '12', 'الثاني عشر': '12',
            'ثالث عشر': '13', 'الثالث عشر': '13',
            'رابع عشر': '14', 'الرابع عشر': '14',
            'خامس عشر': '15', 'الخامس عشر': '15',
            'سادس عشر': '16', 'السادس عشر': '16',
            'سابع عشر': '17', 'السابع عشر': '17',
            'ثامن عشر': '18', 'الثامن عشر': '18',
            'تاسع عشر': '19', 'التاسع عشر': '19',
            # أرقام مركبة (11-19) - مؤنثة
            'حادية عشرة': '11', 'الحادية عشرة': '11',
            'ثانية عشرة': '12', 'الثانية عشرة': '12',
            'ثالثة عشرة': '13', 'الثالثة عشرة': '13',
            'رابعة عشرة': '14', 'الرابعة عشرة': '14',
            'خامسة عشرة': '15', 'الخامسة عشرة': '15',
            'سادسة عشرة': '16', 'السادسة عشرة': '16',
            'سابعة عشرة': '17', 'السابعة عشرة': '17',
            'ثامنة عشرة': '18', 'الثامنة عشرة': '18',
            'تاسعة عشرة': '19', 'التاسعة عشرة': '19',
            # العشرينات (20-29)
            'عشرون': '20', 'العشرون': '20',
            'حادية والعشرون': '21', 'الحادية والعشرون': '21', 'واحد وعشرون': '21',
            'ثانية والعشرون': '22', 'الثانية والعشرون': '22', 'اثنان وعشرون': '22',
            'ثالثة والعشرون': '23', 'الثالثة والعشرون': '23', 'ثلاثة وعشرون': '23',
            'رابعة والعشرون': '24', 'الرابعة والعشرون': '24', 'أربعة وعشرون': '24',
            'خامسة والعشرون': '25', 'الخامسة والعشرون': '25', 'خمسة وعشرون': '25',
            'سادسة والعشرون': '26', 'السادسة والعشرون': '26', 'ستة وعشرون': '26',
            'سابعة والعشرون': '27', 'السابعة والعشرون': '27', 'سبعة وعشرون': '27',
            'ثامنة والعشرون': '28', 'الثامنة والعشرون': '28', 'ثمانية وعشرون': '28',
            'تاسعة والعشرون': '29', 'التاسعة والعشرون': '29', 'تسعة وعشرون': '29',
            # الثلاثينات وما بعدها
            'ثلاثون': '30', 'الثلاثون': '30',
            'أربعون': '40', 'الأربعون': '40',
            'خمسون': '50', 'الخمسون': '50',
            # الأرقام الهندية
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
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
        uploaded_by: Optional[int] = None,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a legal document and extract hierarchical structure
        
        Args:
            file_path: Path to the document file
            law_source_details: Details for creating/updating law source
            uploaded_by: User ID who uploaded the document
            law_source_id: Optional existing LawSource ID (if already created)
        """
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
                document_structure, law_source_details, uploaded_by, law_source_id
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
        
        Enhanced detection for Arabic legal documents with multiple TOC detection strategies:
        1. Explicit TOC headers (الفهرس, جدول المحتويات, etc.)
        2. Pattern-based: lines with branch names + page numbers
        3. Sequential: multiple consecutive branch markers without content
        4. "Chapter" prefix pattern (common in TOC entries)
        5. CRITICAL: TOC ends at first "المادة الأولى" without page numbers
        
        Returns list of (start_line, end_line) tuples for TOC sections.
        """
        toc_sections = []
        current_toc_start = None
        
        # ★★★ NEW: Track all lines with "Chapter" prefix to mark entire TOC block ★★★
        chapter_prefix_lines = []
        for i, line in enumerate(lines):
            if re.search(r'^(Chapter|chapter)\s+(ﺍﻟﺒﺎﺏ|الباب|ﺍﻟﻔﺼﻞ|الفصل)', line.strip()):
                chapter_prefix_lines.append(i + 1)  # 1-based line numbering
        
        # If we found "Chapter" prefix lines, mark entire block as TOC
        if len(chapter_prefix_lines) >= 3:  # At least 3 lines with this pattern = TOC
            # Find first and last occurrence
            toc_start = min(chapter_prefix_lines)
            toc_end = max(chapter_prefix_lines)
            
            # Extend to the actual TOC end by checking for first article without page number
            first_article_patterns = [
                r'المادة الأولى',
                r'ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ',
                r'المادة\s+1\s*:',
                r'المادة\s+الاولى'
            ]
            
            page_number_at_end = r'\.+\s*\d+\s*$|\s+\d+\s*$'
            
            for i in range(toc_end, min(toc_end + 20, len(lines))):
                line_original = lines[i].strip()
                
                # Check if this line is first article
                for article_pattern in first_article_patterns:
                    if re.search(article_pattern, line_original, re.IGNORECASE):
                        # Check if it has page number
                        if not re.search(page_number_at_end, line_original):
                            # Found actual first article - TOC ends here
                            toc_end = i
                            break
            
            # Mark this entire block as TOC
            toc_sections.append((toc_start, toc_end))
            logger.info(f"★ Detected TOC block via 'Chapter' prefix pattern: lines {toc_start} to {toc_end} ({len(chapter_prefix_lines)} lines with 'Chapter' prefix)")
            
            # Return early - we found the TOC block
            return toc_sections
        
        # Track branch occurrences to detect duplicates (TOC vs actual content)
        branch_occurrences = {}  # {branch_number: [line_numbers]}
        
        # Patterns that indicate table of contents
        toc_indicators = [
            r'الفهرس',
            r'ﺍﻟﻔﻬﺮﺱ',  # Encoded version
            r'جدول المحتويات',
            r'ﺟﺪﻭﻝ ﺍﻟﻤﺤﺘﻮﻳﺎﺕ',  # Encoded version
            r'المحتويات',
            r'ﺍﻟﻤﺤﺘﻮﻳﺎﺕ',  # Encoded version
            r'محتوى الكتاب',
            r'فهرس المحتويات',
            r'ﻓﻬﺮﺱ ﺍﻟﻤﺤﺘﻮﻳﺎﺕ',  # Encoded version
            r'index',
            r'table of contents',
            r'contents',
            r'فهرس',
            r'ﻓﻬﺮﺱ'
        ]
        
        # Also detect TOC by pattern: chapter/section names followed by page numbers
        # This is common in Arabic legal documents
        toc_pattern_detected = False
        
        # Patterns that indicate end of table of contents
        # المتطلب الحاسم: يجب أن ينتهي جدول المحتويات عند أول ظهور لـ "المادة الأولى" بدون أرقام صفحات
        toc_end_indicators = [
            r'المادة الأولى',      # المادة الأولى (عادي)
            r'ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ',     # المادة الأولى (encoded)
            r'المادة\s+1\s*:',     # المادة 1:
            r'المادة\s+الاولى',    # تهجئة بديلة
            r'مادة\s+1\s*:',       # مادة 1:
            r'الفصل الأول',
            r'الباب الأول',
            r'بداية النص',
            r'start of text',
            r'beginning of document'
        ]
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            line_original = line.strip()
            
            # Check for TOC start indicators
            if current_toc_start is None:
                # Check explicit TOC indicators
                for indicator in toc_indicators:
                    if re.search(indicator, line_clean, re.IGNORECASE):
                        current_toc_start = i + 1  # 1-based line numbering
                        logger.info(f"Found TOC start at line {current_toc_start}: {line[:50]}...")
                        break
                
                # Detect "Chapter" prefix pattern (common in TOC)
                # Pattern: "Chapter الباب الأول", "Chapter الباب الثاني", etc.
                if not current_toc_start and re.search(r'^(Chapter|chapter)\s+', line_original):
                    # Check if this pattern repeats in next 15 lines (allowing gaps)
                    chapter_prefix_count = 0
                    for lookahead_idx in range(i, min(i + 15, len(lines))):
                        if lookahead_idx < len(lines):
                            if re.search(r'^(Chapter|chapter)\s+', lines[lookahead_idx].strip()):
                                chapter_prefix_count += 1
                    
                    # If we find 3+ lines with "Chapter" prefix within 15 lines, it's TOC
                    # This is lenient enough to allow gaps between TOC entries
                    if chapter_prefix_count >= 3:
                        current_toc_start = i + 1
                        logger.info(f"Found TOC by 'Chapter' prefix pattern (count: {chapter_prefix_count} in 15-line window) at line {current_toc_start}: {line[:50]}...")
                
                # Also detect TOC by pattern: lines ending with page numbers
                # Pattern: "Chapter/Section Name ... 31" or "الباب الأول ... 31"
                if not current_toc_start:
                    # Look for lines that contain chapter/section patterns followed by page numbers
                    page_number_at_end = r'\.+\s*\d+\s*$|\s+\d+\s*$'  # Matches "...31" or "  31"
                    if re.search(page_number_at_end, line.strip()):
                        # Check if this line contains chapter/section keywords
                        chapter_section_keywords = [r'الباب', r'الفصل', r'المادة', r'أولاً', r'ثانياً', r'ﺍﻟﺒﺎﺏ', r'ﺍﻟﻔﺼﻞ', r'ﺍﻟﻤﺎﺩﺓ']
                        for keyword in chapter_section_keywords:
                            if re.search(keyword, line, re.IGNORECASE):
                                # Additional check: look ahead to see if multiple consecutive lines have same pattern
                                # This confirms it's TOC and not just a page reference
                                toc_pattern_count = 0
                                for lookahead_idx in range(i, min(i + 5, len(lines))):
                                    if lookahead_idx < len(lines):
                                        lookahead_line = lines[lookahead_idx].strip()
                                        if re.search(page_number_at_end, lookahead_line):
                                            for kw in chapter_section_keywords:
                                                if re.search(kw, lookahead_line, re.IGNORECASE):
                                                    toc_pattern_count += 1
                                                    break
                                
                                # If we find 3+ consecutive lines with this pattern, it's definitely TOC
                                if toc_pattern_count >= 3:
                                    current_toc_start = i + 1
                                    logger.info(f"Found TOC by pattern (consecutive matches: {toc_pattern_count}) at line {current_toc_start}: {line[:50]}...")
                                    break
                
                # Detect rapid sequential branch markers (TOC listing)
                # If we see multiple branch markers in quick succession without content, it's likely TOC
                if not current_toc_start:
                    chapter_pattern = r'ﺍﻟﺒﺎﺏ|الباب'
                    if re.search(chapter_pattern, line_original):
                        # Count how many branch markers appear in next 10 lines
                        branch_count = 0
                        content_count = 0
                        for lookahead_idx in range(i, min(i + 10, len(lines))):
                            if lookahead_idx < len(lines):
                                lookahead_line = lines[lookahead_idx].strip()
                                if re.search(chapter_pattern, lookahead_line):
                                    branch_count += 1
                                elif len(lookahead_line) > 100:  # Substantial content
                                    content_count += 1
                        
                        # If we have 5+ branches but little content, it's likely TOC
                        if branch_count >= 5 and content_count < 2:
                            current_toc_start = i + 1
                            logger.info(f"Found TOC by rapid branch listing (branches: {branch_count}, content: {content_count}) at line {current_toc_start}: {line[:50]}...")
            
            # Check for TOC end indicators or patterns that suggest end of TOC
            elif current_toc_start is not None:
                should_end_toc = False
                
                # ★★★ المتطلب الحاسم: اكتشاف "المادة الأولى" بدون أرقام صفحات ★★★
                # هذا هو المؤشر الأقوى على نهاية جدول المحتويات وبداية المحتوى الفعلي
                first_article_patterns = [
                    r'المادة الأولى',
                    r'ﺍﻟﻤﺎﺩﺓ ﺍﻷﻭﻟﻰ',
                    r'المادة\s+1\s*:',
                    r'المادة\s+الاولى',
                    r'المادة\s+١'  # رقم عربي
                ]
                
                # Check if line contains first article pattern
                article_found = False
                for article_pattern in first_article_patterns:
                    if re.search(article_pattern, line_original, re.IGNORECASE):
                        article_found = True
                        break
                
                if article_found:
                    # التحقق الحاسم: هل هذا السطر يحتوي على رقم صفحة في النهاية؟
                    page_number_at_end = r'\.+\s*\d+\s*$|\s+\d+\s*$'
                    has_page_number = re.search(page_number_at_end, line_original.strip())
                    
                    if not has_page_number:
                        # ✓ وجدنا "المادة الأولى" بدون رقم صفحة = نهاية جدول المحتويات حتماً
                        should_end_toc = True
                        logger.info(f"✓ TOC ENDED at line {i+1}: Found first article WITHOUT page number: {line[:60]}...")
                    else:
                        # لا يزال في جدول المحتويات (المادة الأولى مع رقم الصفحة)
                        logger.debug(f"Still in TOC at line {i+1}: First article WITH page number: {line[:60]}...")
                
                # Check explicit end indicators (secondary check)
                if not should_end_toc:
                    for indicator in toc_end_indicators:
                        if re.search(indicator, line_clean, re.IGNORECASE):
                            # التأكد من عدم وجود رقم صفحة
                            page_number_at_end = r'\.+\s*\d+\s*$|\s+\d+\s*$'
                            if not re.search(page_number_at_end, line_original.strip()):
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
                
                # Check if we stopped seeing "Chapter" prefix (was in TOC, now in actual content)
                if current_toc_start and i > current_toc_start + 3:
                    # If this line has a branch pattern but NO "Chapter" prefix, might be actual content
                    chapter_pattern = r'ﺍﻟﺒﺎﺏ|الباب'
                    if re.search(chapter_pattern, line_original):
                        if not re.search(r'^(Chapter|chapter)\s+', line_original):
                            # Check if next few lines also lack "Chapter" prefix
                            no_chapter_prefix_count = 0
                            for check_idx in range(i, min(i + 3, len(lines))):
                                if check_idx < len(lines):
                                    check_line = lines[check_idx].strip()
                                    if re.search(chapter_pattern, check_line) and not re.search(r'^(Chapter|chapter)\s+', check_line):
                                        no_chapter_prefix_count += 1
                            
                            # If we consistently don't see "Chapter" prefix anymore, TOC likely ended
                            if no_chapter_prefix_count >= 2:
                                should_end_toc = True
                                logger.info(f"TOC likely ended at line {i} - no more 'Chapter' prefix pattern")
                
                # Check for substantial content following a branch marker (indicates actual content, not TOC)
                if re.search(r'ﺍﻟﺒﺎﺏ|الباب|ﺍﻟﻔﺼﻞ|الفصل', line_original):
                    # Look at next few lines for substantial content
                    content_found = False
                    for check_idx in range(i + 1, min(i + 5, len(lines))):
                        if check_idx < len(lines):
                            check_line = lines[check_idx].strip()
                            # If we find a line with 50+ chars that's not another branch/chapter marker
                            if len(check_line) > 50 and not re.search(r'ﺍﻟﺒﺎﺏ|الباب|ﺍﻟﻔﺼﻞ|الفصل|Chapter', check_line):
                                content_found = True
                                break
                    
                    if content_found:
                        should_end_toc = True
                        logger.info(f"TOC likely ended at line {i} - found substantial content after branch marker")
                
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
            # Additional safety filter: Any line starting with "Chapter" followed by branch markers is TOC
            elif re.search(r'^(Chapter|chapter)\s+(ﺍﻟﺒﺎﺏ|الباب|ﺍﻟﻔﺼﻞ|الفصل)', line.strip()):
                analysis = LineAnalysis(
                    line_number=i,
                    content=line,
                    element_type=ElementType.IGNORE,
                    confidence=1.0,
                    metadata={'reason': 'chapter_prefix_toc'},
                    warnings=[],
                    errors=[]
                )
                logger.debug(f"Line {i} marked as TOC due to 'Chapter' prefix: {line[:50]}...")
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
            # Skip lines marked as IGNORE (e.g., TOC sections, headers, footers)
            if analysis.element_type == ElementType.IGNORE:
                logger.debug(f"Skipping IGNORE line {analysis.line_number}: {analysis.content[:50]}...")
                continue
            
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
        uploaded_by: Optional[int] = None,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Persist the extracted structure to database
        
        Args:
            structure: Parsed document structure
            law_source_details: Law source metadata
            uploaded_by: User ID
            law_source_id: Optional existing LawSource ID to use (prevents duplicate creation)
        """
        try:
            # Use existing law_source if ID is provided, otherwise create new one
            if law_source_id:
                # Fetch existing law source
                result = await self.db.execute(
                    select(LawSource).where(LawSource.id == law_source_id)
                )
                law_source = result.scalars().first()
                
                if not law_source:
                    raise Exception(f"LawSource with ID {law_source_id} not found")
                
                logger.info(f"Using existing LawSource {law_source.id}")
            else:
                # Create new law source (legacy behavior)
                law_source = LawSource(
                    name=law_source_details.get('name', 'Extracted Legal Document') if law_source_details else 'Extracted Legal Document',
                    type=law_source_details.get('type', 'law') if law_source_details else 'law',
                    jurisdiction=law_source_details.get('jurisdiction') if law_source_details else None,
                    issuing_authority=law_source_details.get('issuing_authority') if law_source_details else None,
                    issue_date=law_source_details.get('issue_date') if law_source_details else None,
                    last_update=law_source_details.get('last_update') if law_source_details else None,
                    description=law_source_details.get('description') if law_source_details else None,
                    source_url=law_source_details.get('source_url') if law_source_details else None,
                    knowledge_document_id=law_source_details.get('knowledge_document_id') if law_source_details else None,
                    status='raw'
                )
                
                self.db.add(law_source)
                await self.db.flush()  # Get the ID
                logger.info(f"Created new LawSource {law_source.id}")
            
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

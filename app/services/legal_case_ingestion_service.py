"""
Legal Case Ingestion Service

Complete pipeline for ingesting historical legal cases into the knowledge management system.
Handles file upload, text extraction, section segmentation, and database storage.
"""

import os
import re
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# PDF/DOCX extraction
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from ..models.legal_knowledge import (
    KnowledgeDocument, LegalCase, CaseSection, KnowledgeChunk
)

logger = logging.getLogger(__name__)


class LegalCaseIngestionService:
    """Service for ingesting legal cases from PDF/DOCX files."""
    
    def __init__(self, db: AsyncSession, upload_dir: str = "uploads/legal_cases"):
        """
        Initialize the legal case ingestion service.
        
        Args:
            db: Async database session
            upload_dir: Directory to store uploaded files
        """
        self.db = db
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Arabic section keywords for segmentation
        self.section_patterns = {
            'summary': [
                r'ملخص\s+القضية',
                r'ملخص',
                r'نبذة',
                r'موجز',
                r'الملخص'
            ],
            'facts': [
                r'الوقائع',
                r'وقائع\s+القضية',
                r'وقائع\s+الدعوى',
                r'الواقعة',
                r'الحادثة'
            ],
            'arguments': [
                r'الحجج',
                r'حجج\s+الأطراف',
                r'المرافعات',
                r'الدفوع',
                r'أقوال\s+الأطراف',
                r'دفاع',
                r'الحجة'
            ],
            'ruling': [
                r'الحكم',
                r'منطوق\s+الحكم',
                r'القرار',
                r'حكمت\s+المحكمة',
                r'قررت\s+المحكمة',
                r'المنطوق'
            ],
            'legal_basis': [
                r'الأساس\s+القانوني',
                r'السند\s+القانوني',
                r'التكييف\s+القانوني',
                r'الأسانيد\s+القانونية',
                r'المستند\s+القانوني',
                r'الحيثيات'
            ]
        }
    
    # =====================================================
    # FILE UPLOAD AND HASH CALCULATION
    # =====================================================
    
    async def save_uploaded_case_file(
        self,
        file_content: bytes,
        filename: str,
        uploaded_by: int
    ) -> Tuple[str, str, KnowledgeDocument]:
        """
        Save uploaded file and create KnowledgeDocument record.
        
        Args:
            file_content: Binary content of the uploaded file
            filename: Original filename
            uploaded_by: User ID who uploaded the file
            
        Returns:
            Tuple of (file_path, file_hash, knowledge_document)
            
        Raises:
            ValueError: If file already exists (duplicate hash)
        """
        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for duplicates
        duplicate_check = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.file_hash == file_hash
            )
        )
        existing_doc = duplicate_check.scalar_one_or_none()
        
        if existing_doc:
            raise ValueError(
                f"Duplicate file detected. Document already exists: {existing_doc.title} (ID: {existing_doc.id})"
            )
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix
        safe_filename = f"{timestamp}_{file_hash[:12]}{file_extension}"
        file_path = self.upload_dir / safe_filename
        
        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved file to: {file_path}")
        
        # Create KnowledgeDocument record
        knowledge_doc = KnowledgeDocument(
            title=Path(filename).stem,  # Use filename without extension as title
            category='case',
            file_path=str(file_path),
            file_hash=file_hash,
            source_type='uploaded',
            status='raw',
            uploaded_by=uploaded_by,
            uploaded_at=datetime.utcnow(),
            document_metadata={
                'original_filename': filename,
                'file_size': len(file_content),
                'uploaded_by': uploaded_by
            }
        )
        
        self.db.add(knowledge_doc)
        await self.db.flush()  # Get the ID
        
        logger.info(f"Created KnowledgeDocument ID: {knowledge_doc.id}")
        
        return str(file_path), file_hash, knowledge_doc
    
    # =====================================================
    # TEXT EXTRACTION
    # =====================================================
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF or DOCX file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text as a single string
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If extraction fails
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            return self._extract_pdf_text(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self._extract_docx_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """
        Extract text from PDF file using multiple methods.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        
        # Try PyMuPDF first (best for Arabic)
        if fitz:
            try:
                doc = fitz.open(str(file_path))
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text += page.get_text()
                doc.close()
                
                if text.strip():
                    logger.info(f"Extracted {len(text)} characters using PyMuPDF")
                    return text
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {str(e)}")
        
        # Fallback to pdfplumber
        if pdfplumber and not text.strip():
            try:
                with pdfplumber.open(str(file_path)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                if text.strip():
                    logger.info(f"Extracted {len(text)} characters using pdfplumber")
                    return text
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {str(e)}")
        
        if not text.strip():
            raise RuntimeError(
                "Failed to extract text from PDF. "
                "Please ensure PyMuPDF or pdfplumber is installed."
            )
        
        return text
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        if not DocxDocument:
            raise RuntimeError(
                "python-docx not installed. "
                "Install with: pip install python-docx"
            )
        
        try:
            doc = DocxDocument(str(file_path))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            logger.info(f"Extracted {len(text)} characters from DOCX")
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from DOCX: {str(e)}")
    
    # =====================================================
    # SECTION SEGMENTATION
    # =====================================================
    
    def split_case_sections(self, text: str) -> Dict[str, str]:
        """
        Split case text into logical sections based on Arabic keywords.
        
        Args:
            text: Full text of the legal case
            
        Returns:
            Dictionary with section types as keys and content as values
        """
        sections = {
            'summary': '',
            'facts': '',
            'arguments': '',
            'ruling': '',
            'legal_basis': ''
        }
        
        # Find all section markers with their positions
        section_markers = []
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    section_markers.append({
                        'type': section_type,
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': pattern
                    })
        
        # Sort markers by position
        section_markers.sort(key=lambda x: x['start'])
        
        # Extract content between markers
        for i, marker in enumerate(section_markers):
            section_type = marker['type']
            start = marker['end']
            
            # Find end position (start of next marker or end of text)
            if i + 1 < len(section_markers):
                end = section_markers[i + 1]['start']
            else:
                end = len(text)
            
            content = text[start:end].strip()
            
            # Append to existing content if section already found
            if sections[section_type]:
                sections[section_type] += "\n\n" + content
            else:
                sections[section_type] = content
        
        # If no sections found, put everything in summary
        if not any(sections.values()):
            logger.warning("No section markers found, using entire text as summary")
            sections['summary'] = text
        
        # Log what was found
        found_sections = [k for k, v in sections.items() if v]
        logger.info(f"Found sections: {', '.join(found_sections)}")
        
        return sections
    
    # =====================================================
    # DATABASE STORAGE
    # =====================================================
    
    async def save_case_with_sections(
        self,
        case_metadata: Dict[str, Any],
        sections: Dict[str, str],
        document_id: int
    ) -> LegalCase:
        """
        Save LegalCase and CaseSection records to database.
        
        Args:
            case_metadata: Dictionary containing case metadata
            sections: Dictionary of section content
            document_id: ID of the KnowledgeDocument
            
        Returns:
            Created LegalCase instance
        """
        # Parse date if provided as string
        decision_date = case_metadata.get('decision_date')
        if isinstance(decision_date, str):
            try:
                decision_date = datetime.strptime(decision_date, '%Y-%m-%d').date()
            except:
                decision_date = None
        
        # Create LegalCase record
        legal_case = LegalCase(
            case_number=case_metadata.get('case_number'),
            title=case_metadata.get('title'),
            description=case_metadata.get('description'),
            jurisdiction=case_metadata.get('jurisdiction'),
            court_name=case_metadata.get('court_name'),
            decision_date=decision_date,
            involved_parties=case_metadata.get('involved_parties'),
            document_id=document_id,
            case_type=case_metadata.get('case_type'),
            court_level=case_metadata.get('court_level'),
            case_outcome=case_metadata.get('case_outcome'),
            judge_names=case_metadata.get('judge_names'),
            claim_amount=case_metadata.get('claim_amount'),
            status='raw',
            created_at=datetime.utcnow()
        )
        
        self.db.add(legal_case)
        await self.db.flush()  # Get the ID
        
        logger.info(f"Created LegalCase ID: {legal_case.id}")
        
        # Create CaseSection records
        section_count = 0
        for section_type, content in sections.items():
            if content and content.strip():
                case_section = CaseSection(
                    case_id=legal_case.id,
                    section_type=section_type,
                    content=content.strip(),
                    created_at=datetime.utcnow()
                )
                self.db.add(case_section)
                section_count += 1
        
        await self.db.flush()
        
        logger.info(f"Created {section_count} CaseSection records")
        
        return legal_case
    
    # =====================================================
    # COMPLETE INGESTION PIPELINE
    # =====================================================
    
    async def ingest_legal_case(
        self,
        file_content: bytes,
        filename: str,
        case_metadata: Dict[str, Any],
        uploaded_by: int
    ) -> Dict[str, Any]:
        """
        Complete pipeline: upload file, extract text, segment sections, save to DB.
        
        Args:
            file_content: Binary content of the uploaded file
            filename: Original filename
            case_metadata: Dictionary containing case metadata
            uploaded_by: User ID who uploaded the file
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Step 1: Save file and create KnowledgeDocument
            logger.info(f"Step 1: Saving uploaded file: {filename}")
            file_path, file_hash, knowledge_doc = await self.save_uploaded_case_file(
                file_content, filename, uploaded_by
            )
            
            # Step 2: Extract text from file
            logger.info(f"Step 2: Extracting text from: {file_path}")
            text = self.extract_text(file_path)
            
            if not text or len(text) < 50:
                raise ValueError(
                    f"Extracted text is too short ({len(text)} chars). "
                    "File might be empty or corrupted."
                )
            
            logger.info(f"Extracted {len(text)} characters")
            
            # Step 3: Split into sections
            logger.info(f"Step 3: Splitting text into sections")
            sections = self.split_case_sections(text)
            
            # Step 4: Save case and sections to database
            logger.info(f"Step 4: Saving case and sections to database")
            legal_case = await self.save_case_with_sections(
                case_metadata, sections, knowledge_doc.id
            )
            
            # Update KnowledgeDocument status
            knowledge_doc.status = 'processed'
            knowledge_doc.processed_at = datetime.utcnow()
            
            # Update LegalCase status
            legal_case.status = 'processed'
            
            # Commit transaction
            await self.db.commit()
            
            logger.info(f"✅ Successfully ingested legal case ID: {legal_case.id}")
            
            # Return results
            return {
                'success': True,
                'message': 'Legal case ingested successfully',
                'data': {
                    'knowledge_document_id': knowledge_doc.id,
                    'legal_case_id': legal_case.id,
                    'case_number': legal_case.case_number,
                    'title': legal_case.title,
                    'file_path': file_path,
                    'file_hash': file_hash,
                    'text_length': len(text),
                    'sections_found': [k for k, v in sections.items() if v],
                    'sections_count': sum(1 for v in sections.values() if v)
                }
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to ingest legal case: {str(e)}")
            
            # Clean up file if it was saved
            try:
                if 'file_path' in locals():
                    os.remove(file_path)
            except:
                pass
            
            return {
                'success': False,
                'message': f'Failed to ingest legal case: {str(e)}',
                'data': None
            }
    
    # =====================================================
    # BATCH INGESTION
    # =====================================================
    
    async def ingest_multiple_cases(
        self,
        cases_data: List[Dict[str, Any]],
        uploaded_by: int
    ) -> Dict[str, Any]:
        """
        Ingest multiple legal cases in batch.
        
        Args:
            cases_data: List of dictionaries, each containing:
                - file_content: bytes
                - filename: str
                - case_metadata: dict
            uploaded_by: User ID who uploaded the files
            
        Returns:
            Dictionary with batch ingestion results
        """
        results = {
            'total': len(cases_data),
            'successful': 0,
            'failed': 0,
            'cases': []
        }
        
        for i, case_data in enumerate(cases_data, 1):
            logger.info(f"Processing case {i}/{len(cases_data)}")
            
            result = await self.ingest_legal_case(
                file_content=case_data['file_content'],
                filename=case_data['filename'],
                case_metadata=case_data['case_metadata'],
                uploaded_by=uploaded_by
            )
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['cases'].append({
                'filename': case_data['filename'],
                'success': result['success'],
                'message': result['message'],
                'data': result['data']
            })
        
        return results


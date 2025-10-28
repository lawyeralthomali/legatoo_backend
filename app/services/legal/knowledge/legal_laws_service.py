
import logging
import json
import hashlib
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ....models.legal_knowledge import (
    LawSource, LawArticle,
    KnowledgeDocument, KnowledgeChunk
)
from ....processors.hierarchical_document_processor import HierarchicalDocumentProcessor
from ....parsers.parser_orchestrator import ParserOrchestrator

logger = logging.getLogger(__name__)


def _format_chunk_content(
    article_title: str, 
    article_content: str, 
    article_number: Optional[str] = None
) -> str:
    
    header_parts = []
    
    # Add article number if provided
    if article_number:
        header_parts.append(f"المادة {article_number}")
    
    # Add article title if provided
    if article_title and article_title.strip():
        header_parts.append(article_title.strip())
    
    # Build header
    header = " - ".join(header_parts) if header_parts else ""
    
    # Combine header with content
    if header:
        return f"{header}\n{article_content or ''}".strip()
    
    return (article_content or '').strip()


def _split_to_segments(text: str, seg_chars: int = 1200, overlap: int = 150) -> List[str]:
    
    text = (text or '').strip()
    
    # If text is short enough, return as single segment
    if len(text) <= seg_chars:
        return [text]
    
    segments = []
    start = 0
    
    while start < len(text):
        end = min(start + seg_chars, len(text))
        seg = text[start:end]
        segments.append(seg)
        
        # If we've reached the end, break
        if end == len(text):
            break
        
        # Move start position with overlap
        start = end - overlap
        if start < 0:
            start = 0
    
    return segments


class LegalLawsService:
    """Service for managing legal laws with complete hierarchy support."""

    def __init__(self, db: AsyncSession):
        """Initialize the legal laws service."""
        self.db = db
        self.hierarchical_processor = HierarchicalDocumentProcessor(db)
        self.parser = ParserOrchestrator(self.hierarchical_processor)
    
    def _get_file_extension(self, filename_or_path: str) -> str:
        """Extract file extension from filename or path."""
        if not filename_or_path:
            return ""
        return os.path.splitext(filename_or_path)[1].lower() if '.' in filename_or_path else ""

    


    async def upload_json_law_structure(
        self,
        json_data: Dict[str, Any],
        uploaded_by: int = 1  # Default to user ID 1
    ) -> Dict[str, Any]:
        """
        Upload JSON law structure (legacy method for backwards compatibility).
        
        This method is kept for compatibility with existing upload-json endpoint.
        It creates the KnowledgeDocument and LawSource first, then processes the JSON.
        """
        try:
            logger.info("Starting JSON law structure upload (legacy method)")
            
            # Extract law source data - handle both dict and list formats
            law_sources = json_data.get("law_sources", [])
            if not law_sources:
                return {"success": False, "message": "No law sources found in JSON", "data": None}
            
            # Handle both formats: dict (single law source) or list (multiple law sources)
            if isinstance(law_sources, dict):
                logger.info("📋 Detected single law source (dict format)")
                law_source_data = law_sources
            elif isinstance(law_sources, list):
                if len(law_sources) == 0:
                    return {"success": False, "message": "No law sources found in JSON", "data": None}
                logger.info(f"📋 Detected multiple law sources (list format, count: {len(law_sources)})")
                law_source_data = law_sources[0]
            else:
                return {"success": False, "message": f"Invalid law_sources format: {type(law_sources)}", "data": None}
            processing_report = json_data.get("processing_report", {})
            
            # Generate unique hash for JSON upload based on content
            json_content = json.dumps(json_data, sort_keys=True, ensure_ascii=False)
            unique_hash = hashlib.sha256(json_content.encode('utf-8')).hexdigest()
            
            # Check for duplicate before creating document
            duplicate_check = await self.db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.file_hash == unique_hash)
            )
            existing_doc = duplicate_check.scalar_one_or_none()
            
            if existing_doc:
                logger.warning(f"⚠️ Duplicate file detected: hash {unique_hash[:16]}...")
                
                # Get the related law source if it exists
                law_source_result = await self.db.execute(
                    select(LawSource).where(LawSource.knowledge_document_id == existing_doc.id)
                )
                existing_law_source = law_source_result.scalar_one_or_none()
                
                # Build detailed error message
                error_message = (
                    f"❌ Duplicate file detected: This document has already been uploaded. "
                    f"File hash: {unique_hash[:16]}... "
                    f"Original document ID: {existing_doc.id}, "
                    f"Title: '{existing_doc.title}', "
                    f"Uploaded at: {existing_doc.uploaded_at}"
                )
                
                if existing_law_source:
                    error_message += f", Law Source: '{existing_law_source.name}' (ID: {existing_law_source.id})"
                
                return {
                    "success": False,
                    "message": error_message,
                    "data": {
                        "document_id": existing_doc.id,
                        "document_title": existing_doc.title,
                        "uploaded_at": existing_doc.uploaded_at.isoformat() if existing_doc.uploaded_at else None,
                        "law_source_id": existing_law_source.id if existing_law_source else None,
                        "law_source_name": existing_law_source.name if existing_law_source else None
                    },
                    "errors": [{
                        "field": "file",
                        "message": "This file has already been uploaded. Upload a different file or use the existing document."
                    }]
                }
            
            # Create KnowledgeDocument (no file, just metadata)
            knowledge_doc = KnowledgeDocument(
                title=f"JSON Upload: {law_source_data.get('name', 'Unknown Law')}",
                category="law",
                file_path=f"json_upload_{unique_hash[:8]}.json",  # Unique path for JSON uploads
                file_extension=".json",  # Store file extension
                file_hash=unique_hash,  # Unique hash for JSON uploads
                source_type="uploaded",
                uploaded_by=uploaded_by,
                document_metadata={
                    "source": "json_upload",
                    "processing_report": processing_report
                }
            )
            
            self.db.add(knowledge_doc)
            await self.db.flush()
            logger.info(f"Created KnowledgeDocument {knowledge_doc.id}")
            
            # Create LawSource
            law_source = LawSource(
                knowledge_document_id=knowledge_doc.id,
                name=law_source_data.get("name", "Unknown Law"),
                type=law_source_data.get("type", "law"),
                jurisdiction=law_source_data.get("jurisdiction"),
                issuing_authority=law_source_data.get("issuing_authority"),
                issue_date=self._parse_date(law_source_data.get("issue_date")),
                last_update=self._parse_date(law_source_data.get("last_update")),
                description=law_source_data.get("description"),
                source_url=law_source_data.get("source_url"),
                status="raw"  # Start as raw, will become 'processed' after embeddings are generated
            )
            
            self.db.add(law_source)
            await self.db.flush()
            logger.info(f"Created LawSource {law_source.id}")
            
            # Process law structure - simplify to only process articles directly
            total_articles = 0
            chunk_index = 0
            
            # Check if it has branches structure (hierarchical)
            branches_data = law_source_data.get("branches", [])
        
            # Check if it has direct articles structure
            if law_source_data.get("articles"):
                logger.info(f"📄 Processing direct articles structure")
                articles_data = law_source_data.get("articles", [])
                for article_data in articles_data:
                    # Extract article content - handle both 'text' and 'content' field names
                    article_content = article_data.get("text") or article_data.get("content", "")
                    
                    # Extract article number
                    article_number = article_data.get("article") or article_data.get("article_number", "")
                    
                    # Extract title (default to empty string if not present)
                    article_title = article_data.get("title", "")
                    
                    # Extract order_index - try to extract from article number if not provided
                    order_index = article_data.get("order_index")
                    if order_index is None:
                        # Try to extract number from article number for ordering
                        import re
                        match = re.search(r'\d+', article_number)
                        if match:
                            order_index = int(match.group())
                        else:
                            order_index = total_articles
                    
                    # Create article directly under law source
                    article = LawArticle(
                        law_source_id=law_source.id,
                        article_number=article_number,
                        title=article_title,
                        content=article_content,
                        order_index=order_index,
                        source_document_id=knowledge_doc.id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(article)
                    await self.db.flush()
                    total_articles += 1
                    
                    # Split article content into segments
                    segments = _split_to_segments(article.content)
                    for seg in segments:
                        seg_content = _format_chunk_content(article.title, seg, article.article_number)
                        chunk = KnowledgeChunk(
                            document_id=knowledge_doc.id,
                            chunk_index=chunk_index,
                            content=seg_content,
                            tokens_count=len(seg_content.split()),
                            law_source_id=law_source.id,
                            article_id=article.id,
                            verified_by_admin=False,
                            created_at=datetime.utcnow()
                        )
                        self.db.add(chunk)
                        chunk_index += 1
            
            # Commit all changes
            await self.db.commit()
            
            
            # Prepare response data
            response_data = {
                "law_source": {
                    "id": law_source.id,
                    "name": law_source.name,
                    "type": law_source.type,
                    "jurisdiction": law_source.jurisdiction,
                    "issuing_authority": law_source.issuing_authority
                },
                "statistics": {
                    "total_articles": total_articles,
                    "total_chunks": chunk_index,
                    "processing_report": processing_report
                }
            }
            
            logger.info(f"✅ Successfully uploaded JSON law structure: {total_articles} articles, {chunk_index} chunks (status: raw)")
            
            return {
                "success": True,
                "message": f"Successfully uploaded JSON law structure: {total_articles} articles, {chunk_index} chunks. Status: raw. Use /generate-embeddings endpoint to process and make searchable.",
                "data": response_data
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to upload JSON law structure: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"success": False, "message": f"Failed to upload JSON law structure: {str(e)}", "data": None}

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If no format works, return None
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {str(e)}")
            return None


# ===========================================
    # UPLOAD AND PARSE
    # ===========================================

    async def upload_and_parse_law(
        self,
        file_path: str,
        file_hash: str,
        original_filename: str,
        law_source_details: Dict[str, Any],
        uploaded_by: int,
        use_ai: bool = True,
        fallback_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Upload and parse a legal law document supporting multiple file types.
        
        Supported file types:
        - .json: Fully processed with article extraction
        - .pdf, .docx, .txt: Metadata-only upload (parsing pending)
        
        Args:
            file_path: Path to the uploaded file
            file_hash: SHA-256 hash of the file
            original_filename: Original filename of the uploaded file
            law_source_details: Details for creating the law source
            uploaded_by: User ID who uploaded the document
            use_ai: Whether to use AI parser for supported file types
            fallback_on_failure: Whether to fallback to local parser on AI failure
            
        Returns:
            Dict with success status, message, and data or errors
        """
        try:
            # Step 1: Detect file type
            file_extension = self._get_file_extension(original_filename or file_path)
            logger.info(f"📄 Detected file type: {file_extension}")
            
            # Step 2: Check for duplicate
            duplicate_check = await self.db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.file_hash == file_hash)
            )
            existing_doc = duplicate_check.scalar_one_or_none()
            
            if existing_doc:
                logger.warning(f"⚠️ Duplicate file detected: hash {file_hash[:16]}...")
                
                # Get the related law source if it exists
                law_source_result = await self.db.execute(
                    select(LawSource).where(LawSource.knowledge_document_id == existing_doc.id)
                )
                existing_law_source = law_source_result.scalar_one_or_none()
                
                # Build detailed error message
                error_message = (
                    f"❌ Duplicate file detected: This document has already been uploaded. "
                    f"File hash: {file_hash[:16]}... "
                    f"Original document ID: {existing_doc.id}, "
                    f"Title: '{existing_doc.title}', "
                    f"Uploaded at: {existing_doc.uploaded_at}"
                )
                
                if existing_law_source:
                    error_message += f", Law Source: '{existing_law_source.name}' (ID: {existing_law_source.id})"
                
                return {
                    "success": False,
                    "message": error_message,
                    "data": {
                        "document_id": existing_doc.id,
                        "document_title": existing_doc.title,
                        "uploaded_at": existing_doc.uploaded_at.isoformat() if existing_doc.uploaded_at else None,
                        "law_source_id": existing_law_source.id if existing_law_source else None,
                        "law_source_name": existing_law_source.name if existing_law_source else None
                    },
                    "errors": [{
                        "field": "file",
                        "message": "This file has already been uploaded. Upload a different file or use the existing document."
                    }]
                }
            
            logger.info(f"🚀 Starting law upload and parsing: {law_source_details.get('name')} (Type: {file_extension})")
            
            # Step 3: Create KnowledgeDocument with file extension
            knowledge_doc = KnowledgeDocument(
                title=law_source_details["name"],
                category='law',
                file_path=file_path,
                file_extension=file_extension,  # Store file extension
                file_hash=file_hash,
                source_type='uploaded',
                status='raw',  # Will be updated based on file type
                uploaded_by=uploaded_by,
                uploaded_at=datetime.utcnow(),
                document_metadata={
                    "original_filename": original_filename,
                    "uploaded_by": uploaded_by,
                    "file_type": file_extension
                }
            )
            self.db.add(knowledge_doc)
            await self.db.flush()  # Get the ID
            
            logger.info(f"📄 Created KnowledgeDocument {knowledge_doc.id}")
            
            # Step 4: Create LawSource
            law_source = LawSource(
                name=law_source_details["name"],
                type=law_source_details["type"],
                jurisdiction=law_source_details.get("jurisdiction"),
                issuing_authority=law_source_details.get("issuing_authority"),
                issue_date=law_source_details.get("issue_date"),
                last_update=law_source_details.get("last_update"),
                description=law_source_details.get("description"),
                source_url=law_source_details.get("source_url"),
                knowledge_document_id=knowledge_doc.id,
                status='raw',
                created_at=datetime.utcnow()
            )
            self.db.add(law_source)
            await self.db.flush()  # Get the ID
            
            logger.info(f"📚 Created LawSource {law_source.id}")
            
            # Step 5: Route to appropriate parser based on file type
            if file_extension == '.json':
                # Process JSON file - call the JSON upload logic
                logger.info("🔧 Processing JSON file - using JSON law structure parser")
                return await self._process_json_file(file_path, knowledge_doc, law_source, uploaded_by)
            elif file_extension in ['.pdf', '.docx', '.doc', '.txt']:
                # Create placeholder records for non-JSON files
                logger.info(f"⏳ Processing {file_extension} file - creating metadata records (parsing deferred)")
                return await self._process_non_json_file(file_path, knowledge_doc, law_source, file_extension, uploaded_by, use_ai, fallback_on_failure)
            else:
                # Unsupported file type
                logger.error(f"❌ Unsupported file type: {file_extension}")
                await self.db.rollback()
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_extension}. Supported types: .json, .pdf, .docx, .doc, .txt",
                    "data": None,
                    "errors": [{
                        "field": "file",
                        "message": f"File type {file_extension} is not yet supported for detailed parsing"
                    }]
                }
            
        except Exception as e:
            logger.error(f"Failed to upload and parse law: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to upload and parse law: {str(e)}",
                "data": None
            }
    
    async def _process_json_file(
        self,
        file_path: str,
        knowledge_doc: KnowledgeDocument,
        law_source: LawSource,
        uploaded_by: int
    ) -> Dict[str, Any]:
        """Process JSON file using DocumentUploadService for dual-database support."""
        try:
            logger.info("📋 Processing JSON file with dual-database support...")
            
            # Import DocumentUploadService to use its dual-database logic
            from ....services.legal.knowledge.document_parser_service import DocumentUploadService
            
            # Create DocumentUploadService instance with the same database session
            upload_service = DocumentUploadService(self.db)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Extract title and category from law_source
            title = law_source.name
            category = 'law'  # Default category for laws
            
            # Use DocumentUploadService to process the JSON file
            # This will create entries in SQL but NOT in Chroma yet
            result = await upload_service.upload_document(
                file_content=file_content,
                filename=os.path.basename(file_path),
                title=title,
                category=category,
                uploaded_by=uploaded_by
            )
            
            # Keep status as 'raw' - will be updated to 'processed' after embeddings generation
            law_source.status = 'raw'
            knowledge_doc.status = 'raw'
            await self.db.commit()
            
            # Return the result
            return {
                "success": True,
                "message": f"JSON file uploaded successfully. Created {result.get('chunks_created', 0)} chunks in SQL. Status: raw. Use /generate-embeddings endpoint to generate embeddings and make searchable.",
                "data": {
                    "law_source_id": law_source.id,
                    "document_id": knowledge_doc.id,
                    "total_articles": result.get('articles_processed', 0),
                    "total_chunks": result.get('chunks_created', 0),
                    "status": "raw",
                    "next_step": "Call POST /api/v1/laws/{document_id}/generate-embeddings to generate embeddings",
                    "parser_used": "document_upload_service"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process JSON file: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to process JSON file: {str(e)}",
                "data": None
            }
    
    async def _process_non_json_file(
        self,
        file_path: str,
        knowledge_doc: KnowledgeDocument,
        law_source: LawSource,
        file_extension: str,
        uploaded_by: int,
        use_ai: bool = True,
        fallback_on_failure: bool = True
    ) -> Dict[str, Any]:
        """Process non-JSON files by creating metadata records and marking for deferred parsing."""
        try:
            logger.info(f"⏳ Processing {file_extension} file (parsing deferred)")
            
            # Mark as raw (unprocessed, no embeddings yet)
            knowledge_doc.status = 'raw'
            law_source.status = 'raw'
            
            # Update metadata
            knowledge_doc.document_metadata = {
                **knowledge_doc.document_metadata,
                "parsing_deferred": True,
                "file_extension": file_extension,
                "parser_type": "to_be_implemented"
            }
            
            await self.db.commit()
            
            logger.info(f"✅ Created metadata records for {file_extension} file (Document ID: {knowledge_doc.id}, Law Source ID: {law_source.id})")
            
            return {
                "success": True,
                "message": f"{file_extension.upper()} file uploaded successfully. Metadata records created. Detailed parsing is pending implementation.",
                "data": {
                    "law_source_id": law_source.id,
                    "document_id": knowledge_doc.id,
                    "status": "pending_parsing",
                    "file_type": file_extension,
                    "note": "Detailed article extraction for this file type is not yet implemented"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process {file_extension} file: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to process {file_extension} file: {str(e)}",
                "data": None
            }

    async def _convert_structure_to_hierarchy_dict(self, structure: Any) -> Dict[str, Any]:
        """Convert HierarchicalDocumentProcessor structure to hierarchy dict used downstream."""
        try:
            branches: List[Dict[str, Any]] = []
            chapters_list = getattr(structure, "chapters", [])
            for idx, ch in enumerate(chapters_list):
                branch_number = getattr(ch, "number", None)
                branch_name = getattr(ch, "title", None) or (f"Chapter {idx+1}")
                branch = {
                    "branch_number": branch_number,
                    "branch_name": branch_name,
                    "description": f"Chapter {branch_number}" if branch_number else None,
                    "order_index": getattr(ch, "order_index", idx),
                    "chapters": [],
                }
                # Sections -> chapters
                sections = getattr(ch, "sections", [])
                for s_idx, sec in enumerate(sections):
                    chapter_number = getattr(sec, "number", None)
                    chapter_name = getattr(sec, "title", None) or (f"Section {s_idx+1}")
                    chapter = {
                        "chapter_number": chapter_number,
                        "chapter_name": chapter_name,
                        "description": f"Section {chapter_number}" if chapter_number else None,
                        "order_index": getattr(sec, "order_index", s_idx),
                        "articles": [],
                    }
                    # Articles within section
                    for a_idx, art in enumerate(getattr(sec, "articles", []) or []):
                        article = {
                            "article_number": getattr(art, "number", None),
                            "title": getattr(art, "title", None),
                            "content": getattr(art, "content", None) or "",
                            "keywords": [],
                            "order_index": getattr(art, "order_index", a_idx),
                        }
                        chapter["articles"].append(article)
                    branch["chapters"].append(chapter)
                # Articles directly under chapter
                for a_idx, art in enumerate(getattr(ch, "articles", []) or []):
                    # Wrap direct chapter articles into a synthetic chapter if needed
                    synthetic = {
                        "chapter_number": None,
                        "chapter_name": "General",
                        "description": None,
                        "order_index": 10_000 + a_idx,
                        "articles": [
                            {
                                "article_number": getattr(art, "number", None),
                                "title": getattr(art, "title", None),
                                "content": getattr(art, "content", None) or "",
                                "keywords": [],
                                "order_index": getattr(art, "order_index", a_idx),
                            }
                        ],
                    }
                    branch["chapters"].append(synthetic)
                branches.append(branch)
            return {"branches": branches}
        except Exception as e:
            logger.warning(f"Failed to convert structure to hierarchy dict: {e}")
            return {"branches": []}

    # ===========================================
    # CRUD OPERATIONS
    # ===========================================

    async def list_laws(
        self,
        page: int = 1,
        page_size: int = 20,
        name_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        jurisdiction_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List laws with filtering and pagination."""
        try:
            # Build query with filters
            query = select(LawSource)
            
            if name_filter:
                query = query.where(LawSource.name.ilike(f"%{name_filter}%"))
            if type_filter:
                query = query.where(LawSource.type == type_filter)
            if jurisdiction_filter:
                query = query.where(LawSource.jurisdiction.ilike(f"%{jurisdiction_filter}%"))
            if status_filter:
                query = query.where(LawSource.status == status_filter)
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size).order_by(LawSource.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            laws = result.scalars().all()
            
            # Format response
            laws_data = []
            for law in laws:
                laws_data.append({
                    "id": law.id,
                    "name": law.name,
                    "type": law.type,
                    "jurisdiction": law.jurisdiction,
                    "issuing_authority": law.issuing_authority,
                    "issue_date": law.issue_date.isoformat() if law.issue_date else None,
                    "last_update": law.last_update.isoformat() if law.last_update else None,
                    "description": law.description,
                    "source_url": law.source_url,
                    "status": law.status,
                    "knowledge_document_id": law.knowledge_document_id,  # Needed for generate-embeddings endpoint
                    "created_at": law.created_at.isoformat() if law.created_at else None,
                    "updated_at": law.updated_at.isoformat() if law.updated_at else None
                })
            
            return {
                "success": True,
                "message": f"Retrieved {len(laws_data)} laws",
                "data": {
                    "laws": laws_data,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to list laws: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list laws: {str(e)}",
                "data": None
            }

    async def get_law_tree(self, law_id: int) -> Dict[str, Any]:
        """Get law with all its articles."""
        try:
            # Load law with articles
            query = (
                select(LawSource)
                .options(selectinload(LawSource.articles))
                .where(LawSource.id == law_id)
            )
            
            result = await self.db.execute(query)
            law = result.scalar_one_or_none()
            
            if not law:
                return {
                    "success": False,
                    "message": f"Law with ID {law_id} not found",
                    "data": None
                }
            
            # Build articles list
            articles_data = []
            for article in law.articles:
                articles_data.append({
                    "id": article.id,
                    "article_number": article.article_number,
                    "title": article.title,
                    "content": article.content,
                    "keywords": article.keywords or [],
                    "order_index": article.order_index,
                    "ai_processed_at": article.ai_processed_at.isoformat() if article.ai_processed_at else None,
                    "created_at": article.created_at.isoformat() if article.created_at else None
                })
            
            # Sort articles by order_index
            articles_data.sort(key=lambda x: x["order_index"])
            
            law_data = {
                "id": law.id,
                "name": law.name,
                "type": law.type,
                "jurisdiction": law.jurisdiction,
                "issuing_authority": law.issuing_authority,
                "issue_date": law.issue_date.isoformat() if law.issue_date else None,
                "last_update": law.last_update.isoformat() if law.last_update else None,
                "description": law.description,
                "source_url": law.source_url,
                "status": law.status,
                "articles": articles_data,
                "articles_count": len(articles_data),
                "created_at": law.created_at.isoformat() if law.created_at else None,
                "updated_at": law.updated_at.isoformat() if law.updated_at else None
            }
            
            return {
                "success": True,
                "message": "Law retrieved successfully",
                "data": {"law_source": law_data}
            }
            
        except Exception as e:
            logger.error(f"Failed to get law: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law: {str(e)}",
                "data": None
            }

    async def get_law_metadata(self, law_id: int) -> Dict[str, Any]:
        """Get law metadata only (no hierarchy)."""
        try:
            result = await self.db.execute(
                select(LawSource).where(LawSource.id == law_id)
            )
            law = result.scalar_one_or_none()
            
            if not law:
                return {
                    "success": False,
                    "message": f"Law with ID {law_id} not found",
                    "data": None
                }
            
            law_data = {
                "id": law.id,
                "name": law.name,
                "type": law.type,
                "jurisdiction": law.jurisdiction,
                "issuing_authority": law.issuing_authority,
                "issue_date": law.issue_date.isoformat() if law.issue_date else None,
                "last_update": law.last_update.isoformat() if law.last_update else None,
                "description": law.description,
                "source_url": law.source_url,
                "status": law.status,
                "knowledge_document_id": law.knowledge_document_id,
                "created_at": law.created_at.isoformat() if law.created_at else None,
                "updated_at": law.updated_at.isoformat() if law.updated_at else None
            }
            
            return {
                "success": True,
                "message": "Law metadata retrieved successfully",
                "data": law_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get law metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law metadata: {str(e)}",
                "data": None
            }

    async def update_law(self, law_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update law metadata."""
        try:
            result = await self.db.execute(
                select(LawSource).where(LawSource.id == law_id)
            )
            law = result.scalar_one_or_none()
            
            if not law:
                return {
                    "success": False,
                    "message": f"Law with ID {law_id} not found",
                    "data": None
                }
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(law, field):
                    setattr(law, field, value)
            
            law.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Updated law {law_id}")
            
            return await self.get_law_metadata(law_id)
            
        except Exception as e:
            logger.error(f"Failed to update law: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to update law: {str(e)}",
                "data": None
            }

    async def delete_law(self, law_id: int) -> Dict[str, Any]:
        """Delete law and cascade delete hierarchy."""
        try:
            result = await self.db.execute(
                select(LawSource).where(LawSource.id == law_id)
            )
            law = result.scalar_one_or_none()
            
            if not law:
                return {
                    "success": False,
                    "message": f"Law with ID {law_id} not found",
                    "data": None
                }
            
            law_name = law.name
            
            # Delete will cascade to branches, chapters, articles, chunks
            await self.db.delete(law)
            await self.db.commit()
            
            logger.info(f"Deleted law {law_id}: {law_name}")
            
            return {
                "success": True,
                "message": f"Law '{law_name}' deleted successfully",
                "data": {"deleted_law_id": law_id, "deleted_law_name": law_name}
            }
            
        except Exception as e:
            logger.error(f"Failed to delete law: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to delete law: {str(e)}",
                "data": None
            }

    # ===========================================
    # PROCESSING OPERATIONS
    # ===========================================

    async def reparse_law(self, law_id: int) -> Dict[str, Any]:
        """Reparse PDF and regenerate hierarchy."""
        try:
            # Get law with knowledge document
            result = await self.db.execute(
                select(LawSource)
                .options(selectinload(LawSource.knowledge_document))
                .where(LawSource.id == law_id)
            )
            law = result.scalar_one_or_none()
            
            if not law:
                return {
                    "success": False,
                    "message": f"Law with ID {law_id} not found",
                    "data": None
                }
            
            if not law.knowledge_document:
                return {
                    "success": False,
                    "message": "No associated knowledge document found",
                    "data": None
                }
            
            file_path = law.knowledge_document.file_path
            
            # Delete existing hierarchy (delete articles and chunks)
            await self.db.execute(
                delete(LawArticle).where(LawArticle.law_source_id == law_id)
            )
            await self.db.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.law_source_id == law_id)
            )
            await self.db.commit()
            
            logger.info(f"Deleted existing hierarchy for law {law_id}")
            
            # Reset status
            law.status = 'raw'
            await self.db.commit()
            
            # Reparse using hierarchical processor
            try:
                law_source_details = {
                    "name": law.name,
                    "type": law.type,
                    "jurisdiction": law.jurisdiction,
                    "issuing_authority": law.issuing_authority,
                    "issue_date": law.issue_date,
                    "last_update": law.last_update,
                    "description": law.description,
                    "source_url": law.source_url
                }
                
                parsing_result = await self.hierarchical_processor.process_document(
                    file_path=file_path,
                    law_source_details=law_source_details,
                    uploaded_by=law.knowledge_document.uploaded_by
                )
                
                if not parsing_result.get("success"):
                    return {
                        "success": False,
                        "message": f"Failed to reparse PDF: {parsing_result.get('message')}",
                        "data": None
                    }
                
                hierarchy = parsing_result.get("data", {}).get("hierarchy", {})
                
                # Recreate hierarchy (extract articles directly from structure)
                chunk_index = 0
                branches_data = hierarchy.get("branches", [])
                
                for branch_data in branches_data:
                    for chapter_data in branch_data.get("chapters", []):
                        for article_data in chapter_data.get("articles", []):
                            article = LawArticle(
                                law_source_id=law.id,
                                article_number=article_data.get("article_number"),
                                title=article_data.get("title"),
                                content=article_data.get("content"),
                                keywords=article_data.get("keywords", []),
                                order_index=article_data.get("order_index", 0),
                                source_document_id=law.knowledge_document_id,
                                created_at=datetime.utcnow()
                            )
                            self.db.add(article)
                            await self.db.flush()
                            
                            # Create KnowledgeChunk with title included
                            chunk_content = _format_chunk_content(article.title, article.content)
                            chunk = KnowledgeChunk(
                                document_id=law.knowledge_document_id,
                                chunk_index=chunk_index,
                                content=chunk_content,
                                tokens_count=len(chunk_content.split()),
                                law_source_id=law.id,
                                article_id=article.id,
                                verified_by_admin=False,
                                created_at=datetime.utcnow()
                            )
                            self.db.add(chunk)
                            chunk_index += 1
                
                law.status = 'processed'
                law.updated_at = datetime.utcnow()
                await self.db.commit()
                
                logger.info(f"✅ Successfully reparsed law {law_id}")
                
                return {
                    "success": True,
                    "message": f"Law reparsed successfully. Created {len(branches_data)} branches, {chunk_index} articles.",
                    "data": None
                }
                
            except Exception as parse_error:
                logger.error(f"Reparsing failed: {str(parse_error)}")
                await self.db.rollback()
                return {
                    "success": False,
                    "message": f"Failed to reparse PDF: {str(parse_error)}",
                    "data": None
                }
            
        except Exception as e:
            logger.error(f"Failed to reparse law: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to reparse law: {str(e)}",
                "data": None
            }

    async def analyze_law_with_ai(
        self,
        law_id: int,
        generate_embeddings: bool = True,
        extract_keywords: bool = True,
        update_existing: bool = False,
        processed_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Trigger AI analysis for law articles."""
        try:
            # Get all articles for this law
            result = await self.db.execute(
                select(LawArticle).where(LawArticle.law_source_id == law_id)
            )
            articles = result.scalars().all()
            
            if not articles:
                return {
                    "success": False,
                    "message": "No articles found for this law",
                    "data": None
                }
            
            processed_count = 0
            
            for article in articles:
                # Skip if already processed and not updating
                if article.ai_processed_at and not update_existing:
                    continue
                
                
                # Extract keywords (placeholder - implement with actual AI service)
                if extract_keywords and article.content:
                    # TODO: Implement actual keyword extraction
                    pass
                
                article.ai_processed_at = datetime.utcnow()
                processed_count += 1
            
            await self.db.commit()
            
            # Update law status to indexed
            law_result = await self.db.execute(
                select(LawSource).where(LawSource.id == law_id)
            )
            law = law_result.scalar_one_or_none()
            if law:
                law.status = 'indexed'
                await self.db.commit()
            
            return {
                "success": True,
                "message": f"AI analysis completed for {processed_count} articles",
                "data": {
                    "processed_articles": processed_count,
                    "total_articles": len(articles)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze law with AI: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to analyze law with AI: {str(e)}",
                "data": None
            }

    async def get_law_statistics(self, law_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a law."""
        try:
            # Get counts
            articles_count = await self.db.scalar(
                select(func.count()).select_from(LawArticle).where(LawArticle.law_source_id == law_id)
            )
            
            chunks_count = await self.db.scalar(
                select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.law_source_id == law_id)
            )
            
            verified_chunks = await self.db.scalar(
                select(func.count())
                .select_from(KnowledgeChunk)
                .where(and_(
                    KnowledgeChunk.law_source_id == law_id,
                    KnowledgeChunk.verified_by_admin == True
                ))
            )
            
            processed_articles = await self.db.scalar(
                select(func.count())
                .select_from(LawArticle)
                .where(and_(
                    LawArticle.law_source_id == law_id,
                    LawArticle.ai_processed_at.isnot(None)
                ))
            )
            
            stats_data = {
                "articles_count": articles_count or 0,
                "chunks_count": chunks_count or 0,
                "verified_chunks": verified_chunks or 0,
                "ai_processed_articles": processed_articles or 0
            }
            
            return {
                "success": True,
                "message": "Statistics retrieved successfully",
                "data": stats_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get law statistics: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law statistics: {str(e)}",
                "data": None
            }

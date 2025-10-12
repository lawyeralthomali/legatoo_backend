"""
Arabic Legal Document Processor Service

This service specializes in processing Arabic legal documents (PDF/DOCX) and extracting
law sources and their articles with high accuracy for Arabic legal content.
Follows unified approach and separation of concerns principles.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ....repositories.legal_knowledge_repository import (
    LawSourceRepository, LawArticleRepository, KnowledgeDocumentRepository,
    KnowledgeChunkRepository
)
from ....schemas.legal_knowledge import (
    LawSourceCreate, LawArticleCreate, KnowledgeDocumentCreate,
    KnowledgeChunkCreate, LawSourceTypeEnum, DocumentCategoryEnum,
    SourceTypeEnum, DocumentStatusEnum
)
from ....utils.arabic_legal_processor import (
    DocumentProcessor, ArabicLegalDocumentException
)

logger = logging.getLogger(__name__)


class ArabicLegalDocumentProcessor:
    """Specialized processor for Arabic legal documents."""

    def __init__(self, db: AsyncSession):
        """Initialize the Arabic legal document processor."""
        self.db = db
        self.law_source_repo = LawSourceRepository(db)
        self.law_article_repo = LawArticleRepository(db)
        self.knowledge_doc_repo = KnowledgeDocumentRepository(db)
        self.knowledge_chunk_repo = KnowledgeChunkRepository(db)
        
        # Initialize utility processor
        self.document_processor = DocumentProcessor()

    async def process_legal_document(
        self,
        file_path: str,
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process an Arabic legal document and extract law sources and articles.
        
        Args:
            file_path: Path to the PDF or DOCX file
            law_source_details: Optional existing law source details
            uploaded_by: User ID who uploaded the document
            
        Returns:
            Dict containing processed law source and articles data
        """
        try:
            logger.info(f"Starting processing of Arabic legal document: {file_path}")
            
            # Use utility processor for document processing
            processed_data = await self.document_processor.process_document(
                file_path, law_source_details
            )
            
            # Create knowledge document entry
            doc_title = Path(file_path).stem
            knowledge_doc = await self.knowledge_doc_repo.create_knowledge_document(
                title=doc_title,
                category="law",
                file_path=file_path,
                source_type="uploaded",
                uploaded_by=uploaded_by,
                document_metadata={
                    "processing_status": "processing",
                    "file_type": Path(file_path).suffix.lower(),
                    "total_articles": len(processed_data["articles"])
                }
            )

            # Handle law source creation or retrieval
            if law_source_details and law_source_details.get("id"):
                # Use existing law source
                law_source_id = law_source_details["id"]
                law_source = await self.law_source_repo.get_law_source_by_id(law_source_id)
                if not law_source:
                    return {
                        "success": False,
                        "message": f"Law source with ID {law_source_id} not found",
                        "data": None
                    }
            else:
                # Create new law source from processed data
                law_source = await self.law_source_repo.create_law_source(
                    name=processed_data["law_source"]["name"],
                    type=processed_data["law_source"]["type"],
                    jurisdiction=processed_data["law_source"].get("jurisdiction"),
                    issuing_authority=processed_data["law_source"].get("issuing_authority"),
                    issue_date=processed_data["law_source"].get("issue_date"),
                    last_update=processed_data["law_source"].get("last_update"),
                    description=processed_data["law_source"].get("description"),
                    source_url=processed_data["law_source"].get("source_url"),
                    knowledge_document_id=None,  # TODO: Link to KnowledgeDocument if needed
                    status='raw'
                )
                law_source_id = law_source.id

            # Create law articles in database
            created_articles = []
            for article_data in processed_data["articles"]:
                try:
                    article = await self.law_article_repo.create_law_article(
                        law_source_id=law_source_id,
                        content=article_data["content"],
                        article_number=article_data.get("article_number"),
                        title=article_data.get("title"),
                        keywords=article_data.get("keywords", []),
                        embedding=None  # Will be added later with AI processing
                    )
                    created_articles.append(article)
                    
                    # Create knowledge chunks for long articles
                    if len(article_data["content"]) > 2000:
                        await self._create_article_chunks(article, knowledge_doc.id)
                        
                except Exception as e:
                    logger.error(f"Failed to create article: {str(e)}")
                    continue

            # Update document status
            await self.knowledge_doc_repo.update_document_status(
                knowledge_doc.id, "processed", datetime.now()
            )

            logger.info(f"Successfully processed document: {len(created_articles)} articles extracted")
            
            return {
                "success": True,
                "message": f"Successfully processed document with {len(created_articles)} articles",
                "data": {
                    "law_source": {
                        "id": law_source_id,
                        "name": law_source.name,
                        "type": law_source.type,
                        "jurisdiction": law_source.jurisdiction,
                        "issuing_authority": law_source.issuing_authority,
                        "issue_date": law_source.issue_date.isoformat() if law_source.issue_date else None,
                        "last_update": law_source.last_update.isoformat() if law_source.last_update else None,
                        "description": law_source.description,
                        "source_url": law_source.source_url
                    },
                    "articles": [
                        {
                            "id": article.id,
                            "article_number": article.article_number,
                            "title": article.title,
                            "content": article.content,
                            "keywords": article.keywords or [],
                            "created_at": article.created_at.isoformat()
                        }
                        for article in created_articles
                    ],
                    "knowledge_document": {
                        "id": knowledge_doc.id,
                        "title": knowledge_doc.title,
                        "status": knowledge_doc.status,
                        "processed_at": knowledge_doc.processed_at.isoformat() if knowledge_doc.processed_at else None
                    },
                    "statistics": processed_data["statistics"]
                }
            }

        except ArabicLegalDocumentException as e:
            logger.error(f"Arabic legal document processing error: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data": None
            }
        except Exception as e:
            logger.error(f"Failed to process legal document: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process legal document: {str(e)}",
                "data": None
            }

    async def process_multiple_documents(
        self,
        file_paths: List[str],
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process multiple Arabic legal documents."""
        try:
            results = []
            successful_count = 0
            error_count = 0
            
            for file_path in file_paths:
                try:
                    result = await self.process_legal_document(
                        file_path, law_source_details, uploaded_by
                    )
                    results.append({
                        "file_path": file_path,
                        "success": result["success"],
                        "message": result["message"],
                        "data": result["data"]
                    })
                    
                    if result["success"]:
                        successful_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "message": str(e),
                        "data": None
                    })
                    error_count += 1
            
            return {
                "success": True,
                "message": f"Processed {len(file_paths)} documents: {successful_count} successful, {error_count} failed",
                "data": {
                    "results": results,
                    "statistics": {
                        "total_files": len(file_paths),
                        "successful": successful_count,
                        "failed": error_count
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process multiple documents: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process multiple documents: {str(e)}",
                "data": None
            }

    async def _create_article_chunks(self, article, document_id: int):
        """Create knowledge chunks for long articles."""
        try:
            content = article.content
            if len(content) <= 2000:
                return
            
            # Split content into chunks
            chunk_size = 1500
            chunks = []
            
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                chunks.append(chunk_content)
            
            # Create chunks in database
            for i, chunk_content in enumerate(chunks):
                await self.knowledge_chunk_repo.create_knowledge_chunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_content,
                    tokens_count=len(chunk_content.split()),
                    law_source_ref=article.law_source_id,
                    case_ref=None,
                    term_ref=None
                )
                
        except Exception as e:
            logger.error(f"Failed to create article chunks: {str(e)}")
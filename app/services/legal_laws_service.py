"""
Legal Laws Management Service

This service handles the complete lifecycle of legal laws including:
- Upload and parsing
- Hierarchy extraction (Branches → Chapters → Articles)
- Knowledge chunk creation
- CRUD operations
- AI analysis integration
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..models.legal_knowledge import (
    LawSource, LawBranch, LawChapter, LawArticle,
    KnowledgeDocument, KnowledgeChunk, AnalysisResult
)
from .hierarchical_document_processor import HierarchicalDocumentProcessor
from .enhanced_embedding_service import EnhancedEmbeddingService

logger = logging.getLogger(__name__)


class LegalLawsService:
    """Service for managing legal laws with complete hierarchy support."""

    def __init__(self, db: AsyncSession):
        """Initialize the legal laws service."""
        self.db = db
        self.hierarchical_processor = HierarchicalDocumentProcessor(db)
        self.embedding_service = EnhancedEmbeddingService()

    # ===========================================
    # UPLOAD AND PARSE
    # ===========================================

    async def upload_and_parse_law(
        self,
        file_path: str,
        file_hash: str,
        original_filename: str,
        law_source_details: Dict[str, Any],
        uploaded_by: int
    ) -> Dict[str, Any]:
        """
        Upload PDF, create KnowledgeDocument and LawSource, parse hierarchy.
        
        Workflow:
        1. Check for duplicate via file_hash
        2. Create KnowledgeDocument
        3. Create LawSource
        4. Parse PDF to extract hierarchy
        5. Create branches, chapters, articles
        6. Create knowledge chunks
        7. Update status to 'processed'
        """
        try:
            # Step 1: Check for duplicate
            duplicate_check = await self.db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.file_hash == file_hash)
            )
            existing_doc = duplicate_check.scalar_one_or_none()
            
            if existing_doc:
                return {
                    "success": False,
                    "message": f"Duplicate file detected. Document already exists: {existing_doc.title}",
                    "data": None,
                    "errors": [{
                        "field": "file_hash",
                        "message": f"File already uploaded as document ID {existing_doc.id}"
                    }]
                }
            
            logger.info(f"Starting law upload and parsing: {law_source_details.get('name')}")
            
            # Step 2: Create KnowledgeDocument
            knowledge_doc = KnowledgeDocument(
                title=law_source_details["name"],
                category='law',
                file_path=file_path,
                file_hash=file_hash,
                source_type='uploaded',
                status='raw',
                uploaded_by=uploaded_by,
                uploaded_at=datetime.utcnow(),
                document_metadata={
                    "original_filename": original_filename,
                    "uploaded_by": uploaded_by
                }
            )
            self.db.add(knowledge_doc)
            await self.db.flush()  # Get the ID
            
            logger.info(f"Created KnowledgeDocument {knowledge_doc.id}")
            
            # Step 3: Create LawSource
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
            
            logger.info(f"Created LawSource {law_source.id}")
            
            # Step 4: Parse PDF and extract hierarchy
            try:
                parsing_result = await self.hierarchical_processor.process_document(
                    file_path=file_path,
                    law_source_details=law_source_details,
                    uploaded_by=uploaded_by,
                    law_source_id=law_source.id  # Pass existing LawSource ID to prevent duplicate
                )
                
                if not parsing_result.get("success"):
                    # Rollback on parsing failure
                    await self.db.rollback()
                    return {
                        "success": False,
                        "message": f"Failed to parse PDF: {parsing_result.get('message', 'Unknown error')}",
                        "data": None
                    }
                
                hierarchy = parsing_result.get("data", {}).get("hierarchy", {})
                logger.info(f"Successfully parsed PDF, extracted hierarchy")
                
            except Exception as parse_error:
                logger.error(f"PDF parsing failed: {str(parse_error)}")
                await self.db.rollback()
                return {
                    "success": False,
                    "message": f"Failed to parse PDF: {str(parse_error)}",
                    "data": None
                }
            
            # Step 5: Create hierarchy from parsed data
            chunk_index = 0
            
            # Extract branches from hierarchy
            branches_data = hierarchy.get("branches", [])
            
            for branch_data in branches_data:
                branch = LawBranch(
                    law_source_id=law_source.id,
                    branch_number=branch_data.get("branch_number"),
                    branch_name=branch_data.get("branch_name"),
                    description=branch_data.get("description"),
                    order_index=branch_data.get("order_index", 0),
                    source_document_id=knowledge_doc.id,
                    created_at=datetime.utcnow()
                )
                self.db.add(branch)
                await self.db.flush()
                
                logger.info(f"Created Branch {branch.id}: {branch.branch_name}")
                
                # Extract chapters
                for chapter_data in branch_data.get("chapters", []):
                    chapter = LawChapter(
                        branch_id=branch.id,
                        chapter_number=chapter_data.get("chapter_number"),
                        chapter_name=chapter_data.get("chapter_name"),
                        description=chapter_data.get("description"),
                        order_index=chapter_data.get("order_index", 0),
                        source_document_id=knowledge_doc.id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(chapter)
                    await self.db.flush()
                    
                    logger.info(f"Created Chapter {chapter.id}: {chapter.chapter_name}")
                    
                    # Extract articles
                    for article_data in chapter_data.get("articles", []):
                        article = LawArticle(
                            law_source_id=law_source.id,
                            branch_id=branch.id,
                            chapter_id=chapter.id,
                            article_number=article_data.get("article_number"),
                            title=article_data.get("title"),
                            content=article_data.get("content"),
                            keywords=article_data.get("keywords", []),
                            order_index=article_data.get("order_index", 0),
                            source_document_id=knowledge_doc.id,
                            created_at=datetime.utcnow()
                        )
                        self.db.add(article)
                        await self.db.flush()
                        
                        logger.info(f"Created Article {article.id}: {article.article_number}")
                        
                        # Step 6: Create KnowledgeChunk for article
                        chunk = KnowledgeChunk(
                            document_id=knowledge_doc.id,
                            chunk_index=chunk_index,
                            content=article.content,
                            tokens_count=len(article.content.split()),
                            law_source_id=law_source.id,
                            branch_id=branch.id,
                            chapter_id=chapter.id,
                            article_id=article.id,
                            verified_by_admin=False,
                            created_at=datetime.utcnow()
                        )
                        self.db.add(chunk)
                        chunk_index += 1
            
            # Step 7: Update statuses
            law_source.status = 'processed'
            knowledge_doc.status = 'processed'
            knowledge_doc.processed_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"✅ Successfully uploaded and parsed law {law_source.id}")
            
            # Return full hierarchy tree
            tree_result = await self.get_law_tree(law_source.id)
            
            return {
                "success": True,
                "message": f"Law uploaded and parsed successfully. Created {len(branches_data)} branches, {chunk_index} articles.",
                "data": tree_result.get("data")
            }
            
        except Exception as e:
            logger.error(f"Failed to upload and parse law: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to upload and parse law: {str(e)}",
                "data": None
            }

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
        """Get full hierarchical tree of a law."""
        try:
            # Load law with all relationships
            query = (
                select(LawSource)
                .options(
                    selectinload(LawSource.branches)
                    .selectinload(LawBranch.chapters)
                    .selectinload(LawChapter.articles)
                )
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
            
            # Build tree structure
            branches_data = []
            for branch in law.branches:
                chapters_data = []
                for chapter in branch.chapters:
                    articles_data = []
                    for article in chapter.articles:
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
                    
                    chapters_data.append({
                        "id": chapter.id,
                        "chapter_number": chapter.chapter_number,
                        "chapter_name": chapter.chapter_name,
                        "description": chapter.description,
                        "order_index": chapter.order_index,
                        "articles": articles_data,
                        "articles_count": len(articles_data)
                    })
                
                branches_data.append({
                    "id": branch.id,
                    "branch_number": branch.branch_number,
                    "branch_name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters": chapters_data,
                    "chapters_count": len(chapters_data)
                })
            
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
                "branches": branches_data,
                "branches_count": len(branches_data),
                "created_at": law.created_at.isoformat() if law.created_at else None,
                "updated_at": law.updated_at.isoformat() if law.updated_at else None
            }
            
            return {
                "success": True,
                "message": "Law tree retrieved successfully",
                "data": {"law_source": law_data}
            }
            
        except Exception as e:
            logger.error(f"Failed to get law tree: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law tree: {str(e)}",
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
            
            # Delete existing hierarchy (use delete() correctly)
            await self.db.execute(
                delete(LawBranch).where(LawBranch.law_source_id == law_id)
            )
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
                
                # Recreate hierarchy (same logic as upload_and_parse_law)
                chunk_index = 0
                branches_data = hierarchy.get("branches", [])
                
                for branch_data in branches_data:
                    branch = LawBranch(
                        law_source_id=law.id,
                        branch_number=branch_data.get("branch_number"),
                        branch_name=branch_data.get("branch_name"),
                        description=branch_data.get("description"),
                        order_index=branch_data.get("order_index", 0),
                        source_document_id=law.knowledge_document_id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(branch)
                    await self.db.flush()
                    
                    for chapter_data in branch_data.get("chapters", []):
                        chapter = LawChapter(
                            branch_id=branch.id,
                            chapter_number=chapter_data.get("chapter_number"),
                            chapter_name=chapter_data.get("chapter_name"),
                            description=chapter_data.get("description"),
                            order_index=chapter_data.get("order_index", 0),
                            source_document_id=law.knowledge_document_id,
                            created_at=datetime.utcnow()
                        )
                        self.db.add(chapter)
                        await self.db.flush()
                        
                        for article_data in chapter_data.get("articles", []):
                            article = LawArticle(
                                law_source_id=law.id,
                                branch_id=branch.id,
                                chapter_id=chapter.id,
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
                            
                            chunk = KnowledgeChunk(
                                document_id=law.knowledge_document_id,
                                chunk_index=chunk_index,
                                content=article.content,
                                tokens_count=len(article.content.split()),
                                law_source_id=law.id,
                                branch_id=branch.id,
                                chapter_id=chapter.id,
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
                
                # Generate embeddings
                if generate_embeddings and article.content:
                    try:
                        embedding = await self.embedding_service.generate_embedding(article.content)
                        article.embedding = json.dumps(embedding)
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for article {article.id}: {e}")
                
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
            branches_count = await self.db.scalar(
                select(func.count()).select_from(LawBranch).where(LawBranch.law_source_id == law_id)
            )
            
            chapters_count = await self.db.scalar(
                select(func.count())
                .select_from(LawChapter)
                .join(LawBranch)
                .where(LawBranch.law_source_id == law_id)
            )
            
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
                "branches_count": branches_count or 0,
                "chapters_count": chapters_count or 0,
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

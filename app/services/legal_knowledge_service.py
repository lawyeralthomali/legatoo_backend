"""
Legal Knowledge Management Service

This service provides business logic for managing legal knowledge including
laws, cases, terms, documents, and analysis results.
"""

import logging
import json
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..repositories.legal_knowledge_repository import (
    LawSourceRepository, LawArticleRepository, LegalCaseRepository,
    CaseSectionRepository, LegalTermRepository, KnowledgeDocumentRepository,
    KnowledgeChunkRepository, AnalysisResultRepository, KnowledgeLinkRepository,
    KnowledgeMetadataRepository
)
from .arabic_legal_processor import ArabicLegalDocumentProcessor
from .hierarchical_document_processor import HierarchicalDocumentProcessor
from ..schemas.legal_knowledge import (
    LawSourceCreate, LawSourceUpdate, LawArticleCreate, LawArticleUpdate,
    LegalCaseCreate, LegalCaseUpdate, CaseSectionCreate, CaseSectionUpdate,
    LegalTermCreate, LegalTermUpdate, KnowledgeDocumentCreate, KnowledgeDocumentUpdate,
    KnowledgeChunkCreate, KnowledgeChunkUpdate, AnalysisResultCreate,
    KnowledgeLinkCreate, KnowledgeMetadataCreate, LegalKnowledgeSearchRequest,
    KnowledgeStatsResponse, BulkOperationResponse
)

logger = logging.getLogger(__name__)


class LegalKnowledgeService:
    """Main service for legal knowledge management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize legal knowledge service."""
        self.db = db
        
        # Initialize repositories
        self.law_source_repo = LawSourceRepository(db)
        self.law_article_repo = LawArticleRepository(db)
        self.legal_case_repo = LegalCaseRepository(db)
        self.case_section_repo = CaseSectionRepository(db)
        self.legal_term_repo = LegalTermRepository(db)
        self.knowledge_doc_repo = KnowledgeDocumentRepository(db)
        self.knowledge_chunk_repo = KnowledgeChunkRepository(db)
        self.analysis_result_repo = AnalysisResultRepository(db)
        self.knowledge_link_repo = KnowledgeLinkRepository(db)
        self.knowledge_metadata_repo = KnowledgeMetadataRepository(db)
        
        # Initialize Arabic document processor
        self.arabic_processor = ArabicLegalDocumentProcessor(db)

    # ===========================================
    # LAW SOURCES OPERATIONS
    # ===========================================

    async def create_law_source(self, law_source_data: LawSourceCreate) -> Dict[str, Any]:
        """Create a new law source."""
        try:
            law_source = await self.law_source_repo.create_law_source(
                name=law_source_data.name,
                type=law_source_data.type.value,
                jurisdiction=law_source_data.jurisdiction,
                issuing_authority=law_source_data.issuing_authority,
                issue_date=law_source_data.issue_date,
                last_update=law_source_data.last_update,
                description=law_source_data.description,
                source_url=law_source_data.source_url,
                knowledge_document_id=law_source_data.knowledge_document_id,
                status=law_source_data.status or 'raw'
            )
            
            logger.info(f"Created law source {law_source.id}: {law_source.name}")
            return {
                "success": True,
                "message": "Law source created successfully",
                "data": {
                    "id": law_source.id,
                    "name": law_source.name,
                    "type": law_source.type,
                    "jurisdiction": law_source.jurisdiction,
                    "created_at": law_source.created_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create law source: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create law source: {str(e)}",
                "data": None
            }

    async def get_law_source(self, source_id: int) -> Dict[str, Any]:
        """Get law source by ID."""
        try:
            law_source = await self.law_source_repo.get_law_source_by_id(source_id)
            if not law_source:
                return {
                    "success": False,
                    "message": "Law source not found",
                    "data": None
                }
            
            return {
                "success": True,
                "message": "Law source retrieved successfully",
                "data": {
                    "id": law_source.id,
                    "name": law_source.name,
                    "type": law_source.type,
                    "jurisdiction": law_source.jurisdiction,
                    "issuing_authority": law_source.issuing_authority,
                    "issue_date": law_source.issue_date,
                    "last_update": law_source.last_update,
                    "description": law_source.description,
                    "source_url": law_source.source_url,
                    "knowledge_document_id": law_source.knowledge_document_id,
                    "status": law_source.status,
                    "created_at": law_source.created_at,
                    "updated_at": law_source.updated_at,
                    "articles": [
                        {
                            "id": article.id,
                            "article_number": article.article_number,
                            "title": article.title,
                            "content": article.content[:200] + "..." if len(article.content) > 200 else article.content
                        }
                        for article in law_source.articles
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get law source {source_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law source: {str(e)}",
                "data": None
            }

    async def get_law_sources(
        self,
        skip: int = 0,
        limit: int = 20,
        type: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get law sources with filtering and pagination."""
        try:
            sources, total = await self.law_source_repo.get_law_sources(
                skip=skip, limit=limit, type=type, jurisdiction=jurisdiction
            )
            
            return {
                "success": True,
                "message": "Law sources retrieved successfully",
                "data": {
                    "sources": [
                        {
                            "id": source.id,
                            "name": source.name,
                            "type": source.type,
                            "jurisdiction": source.jurisdiction,
                            "issuing_authority": source.issuing_authority,
                            "issue_date": source.issue_date,
                            "created_at": source.created_at
                        }
                        for source in sources
                    ],
                    "total": total,
                    "page": skip // limit + 1,
                    "size": limit
                }
            }
        except Exception as e:
            logger.error(f"Failed to get law sources: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law sources: {str(e)}",
                "data": None
            }

    async def search_law_sources(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """Search law sources by name or description."""
        try:
            sources = await self.law_source_repo.search_law_sources(search_term, limit)
            
            return {
                "success": True,
                "message": "Search completed successfully",
                "data": {
                    "results": [
                        {
                            "id": source.id,
                            "name": source.name,
                            "type": source.type,
                            "jurisdiction": source.jurisdiction,
                            "description": source.description[:200] + "..." if source.description and len(source.description) > 200 else source.description
                        }
                        for source in sources
                    ],
                    "total": len(sources),
                    "query": search_term
                }
            }
        except Exception as e:
            logger.error(f"Failed to search law sources: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search law sources: {str(e)}",
                "data": None
            }

    async def update_law_source(self, source_id: int, update_data: LawSourceUpdate) -> Dict[str, Any]:
        """Update law source."""
        try:
            # Convert Pydantic model to dict, excluding None values
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            
            law_source = await self.law_source_repo.update_law_source(source_id, **update_dict)
            if not law_source:
                return {
                    "success": False,
                    "message": "Law source not found",
                    "data": None
                }
            
            return {
                "success": True,
                "message": "Law source updated successfully",
                "data": {
                    "id": law_source.id,
                    "name": law_source.name,
                    "type": law_source.type,
                    "updated_at": law_source.updated_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to update law source {source_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update law source: {str(e)}",
                "data": None
            }

    async def delete_law_source(self, source_id: int) -> Dict[str, Any]:
        """Delete law source and all its articles."""
        try:
            success = await self.law_source_repo.delete_law_source(source_id)
            if not success:
                return {
                    "success": False,
                    "message": "Law source not found",
                    "data": None
                }
            
            return {
                "success": True,
                "message": "Law source deleted successfully",
                "data": {"deleted_id": source_id}
            }
        except Exception as e:
            logger.error(f"Failed to delete law source {source_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete law source: {str(e)}",
                "data": None
            }

    # ===========================================
    # LAW ARTICLES OPERATIONS
    # ===========================================

    async def create_law_article(self, article_data: LawArticleCreate) -> Dict[str, Any]:
        """Create a new law article."""
        try:
            article = await self.law_article_repo.create_law_article(
                law_source_id=article_data.law_source_id,
                content=article_data.content,
                article_number=article_data.article_number,
                title=article_data.title,
                keywords=article_data.keywords,
                embedding=article_data.embedding
            )
            
            logger.info(f"Created law article {article.id}")
            return {
                "success": True,
                "message": "Law article created successfully",
                "data": {
                    "id": article.id,
                    "law_source_id": article.law_source_id,
                    "article_number": article.article_number,
                    "title": article.title,
                    "created_at": article.created_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create law article: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create law article: {str(e)}",
                "data": None
            }

    async def get_law_articles_by_source(
        self,
        law_source_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get articles for a specific law source."""
        try:
            articles = await self.law_article_repo.get_articles_by_source(
                law_source_id, skip, limit
            )
            
            return {
                "success": True,
                "message": "Law articles retrieved successfully",
                "data": {
                    "articles": [
                        {
                            "id": article.id,
                            "article_number": article.article_number,
                            "title": article.title,
                            "content": article.content[:300] + "..." if len(article.content) > 300 else article.content,
                            "keywords": article.keywords,
                            "created_at": article.created_at
                        }
                        for article in articles
                    ],
                    "law_source_id": law_source_id,
                    "total": len(articles)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get law articles: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get law articles: {str(e)}",
                "data": None
            }

    async def search_law_articles(
        self,
        search_term: str,
        law_source_id: Optional[int] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search law articles by content or title."""
        try:
            articles = await self.law_article_repo.search_articles(
                search_term, law_source_id, limit
            )
            
            return {
                "success": True,
                "message": "Search completed successfully",
                "data": {
                    "results": [
                        {
                            "id": article.id,
                            "law_source_id": article.law_source_id,
                            "article_number": article.article_number,
                            "title": article.title,
                            "content": article.content[:200] + "..." if len(article.content) > 200 else article.content,
                            "keywords": article.keywords
                        }
                        for article in articles
                    ],
                    "total": len(articles),
                    "query": search_term
                }
            }
        except Exception as e:
            logger.error(f"Failed to search law articles: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search law articles: {str(e)}",
                "data": None
            }

    # ===========================================
    # LEGAL CASES OPERATIONS
    # ===========================================

    async def create_legal_case(self, case_data: LegalCaseCreate) -> Dict[str, Any]:
        """Create a new legal case."""
        try:
            case = await self.legal_case_repo.create_legal_case(
                title=case_data.title,
                case_number=case_data.case_number,
                description=case_data.description,
                jurisdiction=case_data.jurisdiction,
                court_name=case_data.court_name,
                decision_date=case_data.decision_date,
                involved_parties=case_data.involved_parties,
                pdf_path=case_data.pdf_path,
                source_reference=case_data.source_reference,
                case_type=case_data.case_type,
                court_level=case_data.court_level,
                case_outcome=case_data.case_outcome,
                judge_names=case_data.judge_names,
                claim_amount=case_data.claim_amount
            )
            
            logger.info(f"Created legal case {case.id}: {case.title}")
            return {
                "success": True,
                "message": "Legal case created successfully",
                "data": {
                    "id": case.id,
                    "case_number": case.case_number,
                    "title": case.title,
                    "jurisdiction": case.jurisdiction,
                    "court_name": case.court_name,
                    "case_type": case.case_type,
                    "court_level": case.court_level,
                    "case_outcome": case.case_outcome,
                    "judge_names": case.judge_names,
                    "claim_amount": case.claim_amount,
                    "created_at": case.created_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create legal case: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create legal case: {str(e)}",
                "data": None
            }

    async def get_legal_cases(
        self,
        skip: int = 0,
        limit: int = 20,
        jurisdiction: Optional[str] = None,
        court_name: Optional[str] = None,
        case_type: Optional[str] = None,
        court_level: Optional[str] = None,
        case_outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get legal cases with filtering and pagination."""
        try:
            cases, total = await self.legal_case_repo.get_cases(
                skip=skip, limit=limit, jurisdiction=jurisdiction, court_name=court_name,
                case_type=case_type, court_level=court_level, case_outcome=case_outcome
            )
            
            return {
                "success": True,
                "message": "Legal cases retrieved successfully",
                "data": {
                    "cases": [
                        {
                            "id": case.id,
                            "case_number": case.case_number,
                            "title": case.title,
                            "jurisdiction": case.jurisdiction,
                            "court_name": case.court_name,
                            "decision_date": case.decision_date,
                            "case_type": case.case_type,
                            "court_level": case.court_level,
                            "case_outcome": case.case_outcome,
                            "judge_names": case.judge_names,
                            "claim_amount": case.claim_amount,
                            "created_at": case.created_at
                        }
                        for case in cases
                    ],
                    "total": total,
                    "page": skip // limit + 1,
                    "size": limit
                }
            }
        except Exception as e:
            logger.error(f"Failed to get legal cases: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get legal cases: {str(e)}",
                "data": None
            }

    async def search_legal_cases(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """Search legal cases by title, description, or case number."""
        try:
            cases = await self.legal_case_repo.search_cases(search_term, limit)
            
            return {
                "success": True,
                "message": "Search completed successfully",
                "data": {
                    "results": [
                        {
                            "id": case.id,
                            "case_number": case.case_number,
                            "title": case.title,
                            "jurisdiction": case.jurisdiction,
                            "court_name": case.court_name,
                            "decision_date": case.decision_date,
                            "case_type": case.case_type,
                            "court_level": case.court_level,
                            "case_outcome": case.case_outcome,
                            "judge_names": case.judge_names,
                            "claim_amount": case.claim_amount,
                            "description": case.description[:200] + "..." if case.description and len(case.description) > 200 else case.description
                        }
                        for case in cases
                    ],
                    "total": len(cases),
                    "query": search_term
                }
            }
        except Exception as e:
            logger.error(f"Failed to search legal cases: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search legal cases: {str(e)}",
                "data": None
            }

    # ===========================================
    # LEGAL TERMS OPERATIONS
    # ===========================================

    async def create_legal_term(self, term_data: LegalTermCreate) -> Dict[str, Any]:
        """Create a new legal term."""
        try:
            term = await self.legal_term_repo.create_legal_term(
                term=term_data.term,
                definition=term_data.definition,
                source=term_data.source,
                related_terms=term_data.related_terms,
                embedding=term_data.embedding
            )
            
            logger.info(f"Created legal term {term.id}: {term.term}")
            return {
                "success": True,
                "message": "Legal term created successfully",
                "data": {
                    "id": term.id,
                    "term": term.term,
                    "definition": term.definition,
                    "source": term.source,
                    "created_at": term.created_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create legal term: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create legal term: {str(e)}",
                "data": None
            }

    async def search_legal_terms(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """Search legal terms by term or definition."""
        try:
            terms = await self.legal_term_repo.search_terms(search_term, limit)
            
            return {
                "success": True,
                "message": "Search completed successfully",
                "data": {
                    "results": [
                        {
                            "id": term.id,
                            "term": term.term,
                            "definition": term.definition,
                            "source": term.source,
                            "related_terms": term.related_terms
                        }
                        for term in terms
                    ],
                    "total": len(terms),
                    "query": search_term
                }
            }
        except Exception as e:
            logger.error(f"Failed to search legal terms: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search legal terms: {str(e)}",
                "data": None
            }

    # ===========================================
    # KNOWLEDGE DOCUMENTS OPERATIONS
    # ===========================================

    async def create_knowledge_document(self, doc_data: KnowledgeDocumentCreate) -> Dict[str, Any]:
        """Create a new knowledge document."""
        try:
            document = await self.knowledge_doc_repo.create_knowledge_document(
                title=doc_data.title,
                category=doc_data.category.value,
                file_path=doc_data.file_path,
                source_type=doc_data.source_type.value,
                uploaded_by=doc_data.uploaded_by,
                document_metadata=doc_data.document_metadata
            )
            
            logger.info(f"Created knowledge document {document.id}: {document.title}")
            return {
                "success": True,
                "message": "Knowledge document created successfully",
                "data": {
                    "id": document.id,
                    "title": document.title,
                    "category": document.category,
                    "status": document.status,
                    "uploaded_at": document.uploaded_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create knowledge document: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create knowledge document: {str(e)}",
                "data": None
            }

    async def get_knowledge_documents(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get knowledge documents with filtering and pagination."""
        try:
            documents, total = await self.knowledge_doc_repo.get_documents(
                skip=skip, limit=limit, category=category, status=status, uploaded_by=uploaded_by
            )
            
            return {
                "success": True,
                "message": "Knowledge documents retrieved successfully",
                "data": {
                    "documents": [
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "category": doc.category,
                            "status": doc.status,
                            "source_type": doc.source_type,
                            "uploaded_at": doc.uploaded_at,
                            "processed_at": doc.processed_at
                        }
                        for doc in documents
                    ],
                    "total": total,
                    "page": skip // limit + 1,
                    "size": limit
                }
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge documents: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get knowledge documents: {str(e)}",
                "data": None
            }

    # ===========================================
    # ANALYSIS RESULTS OPERATIONS
    # ===========================================

    async def create_analysis_result(self, result_data: AnalysisResultCreate) -> Dict[str, Any]:
        """Create a new analysis result."""
        try:
            result = await self.analysis_result_repo.create_analysis_result(
                document_id=result_data.document_id,
                analysis_type=result_data.analysis_type.value,
                output=result_data.output,
                model_version=result_data.model_version,
                confidence=result_data.confidence
            )
            
            logger.info(f"Created analysis result {result.id}")
            return {
                "success": True,
                "message": "Analysis result created successfully",
                "data": {
                    "id": result.id,
                    "document_id": result.document_id,
                    "analysis_type": result.analysis_type,
                    "confidence": result.confidence,
                    "created_at": result.created_at
                }
            }
        except Exception as e:
            logger.error(f"Failed to create analysis result: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create analysis result: {str(e)}",
                "data": None
            }

    # ===========================================
    # STATISTICS AND ANALYTICS
    # ===========================================

    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge statistics."""
        try:
            # Get counts from repositories
            law_sources, _ = await self.law_source_repo.get_law_sources(limit=1000)
            cases, _ = await self.legal_case_repo.get_cases(limit=1000)
            documents, _ = await self.knowledge_doc_repo.get_documents(limit=1000)
            
            # Count articles and terms
            total_articles = sum(len(source.articles) for source in law_sources)
            
            # Get terms count (simplified - in real implementation, you'd have a count method)
            terms = await self.legal_term_repo.search_terms("", limit=1000)
            total_terms = len(terms)
            
            # Count chunks (simplified)
            chunks = await self.knowledge_chunk_repo.search_chunks("", limit=1000)
            total_chunks = len(chunks)
            
            # Group by type/jurisdiction/category
            sources_by_type = {}
            for source in law_sources:
                sources_by_type[source.type] = sources_by_type.get(source.type, 0) + 1
            
            cases_by_jurisdiction = {}
            for case in cases:
                if case.jurisdiction:
                    cases_by_jurisdiction[case.jurisdiction] = cases_by_jurisdiction.get(case.jurisdiction, 0) + 1
            
            documents_by_category = {}
            for doc in documents:
                documents_by_category[doc.category] = documents_by_category.get(doc.category, 0) + 1
            
            return {
                "success": True,
                "message": "Statistics retrieved successfully",
                "data": {
                    "total_law_sources": len(law_sources),
                    "total_articles": total_articles,
                    "total_cases": len(cases),
                    "total_terms": total_terms,
                    "total_documents": len(documents),
                    "total_chunks": total_chunks,
                    "sources_by_type": sources_by_type,
                    "cases_by_jurisdiction": cases_by_jurisdiction,
                    "documents_by_category": documents_by_category
                }
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge statistics: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get knowledge statistics: {str(e)}",
                "data": None
            }

    # ===========================================
    # ARABIC DOCUMENT PROCESSING
    # ===========================================

    async def process_arabic_legal_document(
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
            result = await self.arabic_processor.process_legal_document(
                file_path, law_source_details, uploaded_by
            )
            
            if result["success"]:
                logger.info(f"Successfully processed Arabic legal document: {file_path}")
            else:
                logger.error(f"Failed to process Arabic legal document: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process Arabic legal document: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process Arabic legal document: {str(e)}",
                "data": None
            }

    async def process_multiple_arabic_documents(
        self,
        file_paths: List[str],
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process multiple Arabic legal documents.
        
        Args:
            file_paths: List of paths to PDF or DOCX files
            law_source_details: Optional existing law source details
            uploaded_by: User ID who uploaded the documents
            
        Returns:
            Dict containing processing results for all documents
        """
        try:
            result = await self.arabic_processor.process_multiple_documents(
                file_paths, law_source_details, uploaded_by
            )
            
            if result["success"]:
                logger.info(f"Successfully processed {len(file_paths)} Arabic legal documents")
            else:
                logger.error(f"Failed to process multiple Arabic legal documents: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process multiple Arabic legal documents: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process multiple Arabic legal documents: {str(e)}",
                "data": None
            }

    async def extract_law_source_metadata(
        self,
        text: str,
        existing_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract law source metadata from Arabic text.
        
        Args:
            text: Arabic legal text
            existing_details: Optional existing law source details to merge
            
        Returns:
            Dict containing detected law source metadata
        """
        try:
            detected_info = await self.arabic_processor._detect_law_source_from_text(text)
            
            if existing_details:
                # Merge existing details with detected ones
                detected_info.update({k: v for k, v in existing_details.items() if v is not None})
            
            return {
                "success": True,
                "message": "Law source metadata extracted successfully",
                "data": detected_info
            }
            
        except Exception as e:
            logger.error(f"Failed to extract law source metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to extract law source metadata: {str(e)}",
                "data": None
            }

    async def extract_articles_from_text(
        self,
        text: str,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract articles from Arabic legal text.
        
        Args:
            text: Arabic legal text
            law_source_id: Optional law source ID to associate articles with
            
        Returns:
            Dict containing extracted articles
        """
        try:
            articles = await self.arabic_processor._extract_articles_from_text(text)
            
            # If law_source_id is provided, create articles in database
            if law_source_id and articles:
                created_articles = []
                for article_data in articles:
                    try:
                        article = await self.law_article_repo.create_law_article(
                            law_source_id=law_source_id,
                            content=article_data["content"],
                            article_number=article_data.get("article_number"),
                            title=article_data.get("title"),
                            keywords=article_data.get("keywords", []),
                            embedding=None
                        )
                        created_articles.append(article)
                    except Exception as e:
                        logger.error(f"Failed to create article: {str(e)}")
                        continue
                
                return {
                    "success": True,
                    "message": f"Extracted and created {len(created_articles)} articles",
                    "data": {
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
                        "total_articles": len(created_articles)
                    }
                }
            else:
                return {
                    "success": True,
                    "message": f"Extracted {len(articles)} articles from text",
                    "data": {
                        "articles": articles,
                        "total_articles": len(articles)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to extract articles from text: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to extract articles from text: {str(e)}",
                "data": None
            }

    # ===========================================
    # UNIFIED SEARCH
    # ===========================================

    async def unified_search(self, search_request: LegalKnowledgeSearchRequest) -> Dict[str, Any]:
        """Perform unified search across all knowledge types."""
        try:
            results = []
            total_results = 0
            
            # Search law sources
            if search_request.search_type in ["all", "laws", None]:
                law_sources = await self.law_source_repo.search_law_sources(
                    search_request.query, search_request.limit
                )
                for source in law_sources:
                    results.append({
                        "type": "law_source",
                        "id": source.id,
                        "title": source.name,
                        "content": source.description or "",
                        "metadata": {
                            "type": source.type,
                            "jurisdiction": source.jurisdiction,
                            "issuing_authority": source.issuing_authority
                        }
                    })
                total_results += len(law_sources)
            
            # Search law articles
            if search_request.search_type in ["all", "laws", None]:
                articles = await self.law_article_repo.search_articles(
                    search_request.query, None, search_request.limit
                )
                for article in articles:
                    results.append({
                        "type": "law_article",
                        "id": article.id,
                        "title": article.title or f"Article {article.article_number}",
                        "content": article.content,
                        "metadata": {
                            "law_source_id": article.law_source_id,
                            "article_number": article.article_number,
                            "keywords": article.keywords
                        }
                    })
                total_results += len(articles)
            
            # Search legal cases
            if search_request.search_type in ["all", "cases", None]:
                cases = await self.legal_case_repo.search_cases(
                    search_request.query, search_request.limit
                )
                for case in cases:
                    results.append({
                        "type": "legal_case",
                        "id": case.id,
                        "title": case.title,
                        "content": case.description or "",
                        "metadata": {
                            "case_number": case.case_number,
                            "jurisdiction": case.jurisdiction,
                            "court_name": case.court_name,
                            "decision_date": case.decision_date,
                            "case_type": case.case_type,
                            "court_level": case.court_level,
                            "case_outcome": case.case_outcome,
                            "judge_names": case.judge_names,
                            "claim_amount": case.claim_amount
                        }
                    })
                total_results += len(cases)
            
            # Search legal terms
            if search_request.search_type in ["all", "terms", None]:
                terms = await self.legal_term_repo.search_terms(
                    search_request.query, search_request.limit
                )
                for term in terms:
                    results.append({
                        "type": "legal_term",
                        "id": term.id,
                        "title": term.term,
                        "content": term.definition or "",
                        "metadata": {
                            "source": term.source,
                            "related_terms": term.related_terms
                        }
                    })
                total_results += len(terms)
            
            return {
                "success": True,
                "message": "Unified search completed successfully",
                "data": {
                    "results": results,
                    "total": total_results,
                    "query": search_request.query,
                    "search_type": search_request.search_type or "all"
                }
            }
        except Exception as e:
            logger.error(f"Failed to perform unified search: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to perform unified search: {str(e)}",
                "data": None
            }
    
    # ===========================================
    # HIERARCHICAL DOCUMENT PROCESSING
    # ===========================================
    
    async def process_arabic_legal_document_hierarchical(
        self,
        file_path: str,
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process Arabic legal document with hierarchical structure extraction.
        
        This method implements the complete workflow for extracting hierarchical
        structure (Chapters → Sections → Articles) from legal documents.
        
        Args:
            file_path: Path to the document file
            law_source_details: Optional metadata for the law source
            uploaded_by: User ID who uploaded the document
            
        Returns:
            Dict containing processing results and extracted structure
        """
        try:
            # Use the hierarchical document processor
            processor = HierarchicalDocumentProcessor(self.db)
            result = await processor.process_document(
                file_path=file_path,
                law_source_details=law_source_details,
                uploaded_by=uploaded_by
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process Arabic legal document hierarchically: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to process Arabic legal document: {str(e)}",
                "data": None
            }
    
    async def validate_document_structure(
        self,
        law_source_id: int,
        validate_numbering: bool = True,
        validate_hierarchy: bool = True,
        detect_gaps: bool = True
    ) -> Dict[str, Any]:
        """
        Validate the hierarchical structure of a processed document.
        
        Args:
            law_source_id: ID of the law source to validate
            validate_numbering: Whether to validate numbering continuity
            validate_hierarchy: Whether to validate parent-child relationships
            detect_gaps: Whether to detect missing elements
            
        Returns:
            Dict containing validation results
        """
        try:
            processor = HierarchicalDocumentProcessor(self.db)
            result = await processor.validate_structure(
                law_source_id=law_source_id,
                validate_numbering=validate_numbering,
                validate_hierarchy=validate_hierarchy,
                detect_gaps=detect_gaps
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to validate document structure: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to validate document structure: {str(e)}",
                "data": None
            }
    
    async def get_document_structure(
        self,
        law_source_id: int
    ) -> Dict[str, Any]:
        """
        Get the complete hierarchical structure of a processed document.
        
        Args:
            law_source_id: ID of the law source
            
        Returns:
            Dict containing the complete document structure
        """
        try:
            # Get law source
            law_source = await self.law_source_repo.get_by_id(law_source_id)
            if not law_source:
                return {
                    "success": False,
                    "message": "Law source not found",
                    "data": None
                }
            
            # Get branches (chapters)
            branches = await self.law_source_repo.get_branches_by_source_id(law_source_id)
            
            structure = {
                "law_source": {
                    "id": law_source.id,
                    "name": law_source.name,
                    "type": law_source.type,
                    "jurisdiction": law_source.jurisdiction,
                    "issuing_authority": law_source.issuing_authority,
                    "issue_date": law_source.issue_date,
                    "last_update": law_source.last_update,
                    "description": law_source.description
                },
                "branches": [],
                "statistics": {
                    "total_branches": 0,
                    "total_chapters": 0,
                    "total_articles": 0
                }
            }
            
            total_chapters = 0
            total_articles = 0
            
            for branch in branches:
                branch_data = {
                    "id": branch.id,
                    "number": branch.branch_number,
                    "name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters": [],
                    "articles": []
                }
                
                # Get chapters (sections) for this branch
                chapters = await self.law_source_repo.get_chapters_by_branch_id(branch.id)
                total_chapters += len(chapters)
                
                for chapter in chapters:
                    chapter_data = {
                        "id": chapter.id,
                        "number": chapter.chapter_number,
                        "name": chapter.chapter_name,
                        "description": chapter.description,
                        "order_index": chapter.order_index,
                        "articles": []
                    }
                    
                    # Get articles for this chapter
                    articles = await self.law_article_repo.get_by_chapter_id(chapter.id)
                    chapter_data["articles"] = [
                        {
                            "id": article.id,
                            "number": article.article_number,
                            "title": article.title,
                            "content": article.content,
                            "order_index": article.order_index,
                            "keywords": article.keywords or [],
                            "created_at": article.created_at
                        }
                        for article in articles
                    ]
                    total_articles += len(articles)
                    
                    branch_data["chapters"].append(chapter_data)
                
                # Get direct articles for this branch (not in any chapter)
                direct_articles = await self.law_article_repo.get_by_branch_id(branch.id)
                branch_data["articles"] = [
                    {
                        "id": article.id,
                        "number": article.article_number,
                        "title": article.title,
                        "content": article.content,
                        "order_index": article.order_index,
                        "keywords": article.keywords or [],
                        "created_at": article.created_at
                    }
                    for article in direct_articles
                ]
                total_articles += len(direct_articles)
                
                structure["branches"].append(branch_data)
            
            # Get orphaned articles (not in any branch/chapter)
            orphaned_articles = await self.law_article_repo.get_orphaned_articles(law_source_id)
            structure["orphaned_articles"] = [
                {
                    "id": article.id,
                    "number": article.article_number,
                    "title": article.title,
                    "content": article.content,
                    "order_index": article.order_index,
                    "keywords": article.keywords or [],
                    "created_at": article.created_at
                }
                for article in orphaned_articles
            ]
            total_articles += len(orphaned_articles)
            
            # Update statistics
            structure["statistics"] = {
                "total_branches": len(branches),
                "total_chapters": total_chapters,
                "total_articles": total_articles,
                "orphaned_articles": len(orphaned_articles)
            }
            
            return {
                "success": True,
                "message": "Document structure retrieved successfully",
                "data": structure
            }
            
        except Exception as e:
            logger.error(f"Failed to get document structure: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get document structure: {str(e)}",
                "data": None
            }

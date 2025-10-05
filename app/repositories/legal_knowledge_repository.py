"""
Legal Knowledge Repository for data access layer.

This module implements the Repository pattern for legal knowledge management,
providing clean separation of data access logic from business logic.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import logging
import json

from ..models.legal_knowledge import (
    LawSource, LawBranch, LawChapter, LawArticle, LegalCase, CaseSection, LegalTerm,
    KnowledgeDocument, KnowledgeChunk, AnalysisResult, KnowledgeLink, KnowledgeMetadata
)
from .base import BaseRepository

logger = logging.getLogger(__name__)


class LawSourceRepository:
    """Repository for legal sources operations."""

    def __init__(self, db: AsyncSession):
        """Initialize law source repository."""
        self.db = db

    async def create_law_source(
        self,
        name: str,
        type: str,
        jurisdiction: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        issue_date: Optional[str] = None,
        last_update: Optional[str] = None,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        knowledge_document_id: Optional[int] = None,
        status: str = 'raw'
    ) -> LawSource:
        """Create a new law source."""
        law_source = LawSource(
            name=name,
            type=type,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            issue_date=issue_date,
            last_update=last_update,
            description=description,
            source_url=source_url,
            knowledge_document_id=knowledge_document_id,
            status=status
        )
        self.db.add(law_source)
        await self.db.commit()
        await self.db.refresh(law_source)
        logger.info(f"Created law source {law_source.id}: {name}")
        return law_source

    async def get_law_source_by_id(self, source_id: int) -> Optional[LawSource]:
        """Get law source by ID with articles preloaded."""
        result = await self.db.execute(
            select(LawSource)
            .options(selectinload(LawSource.articles))
            .where(LawSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_law_sources(
        self,
        skip: int = 0,
        limit: int = 100,
        type: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Tuple[List[LawSource], int]:
        """Get law sources with filtering and pagination."""
        query = select(LawSource)
        count_query = select(func.count()).select_from(LawSource)
        
        filters = []
        if type:
            filters.append(LawSource.type == type)
        if jurisdiction:
            filters.append(LawSource.jurisdiction == jurisdiction)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get sources with pagination
        query = query.order_by(desc(LawSource.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        sources = result.scalars().all()
        
        return sources, total

    async def search_law_sources(self, search_term: str, limit: int = 50) -> List[LawSource]:
        """Search law sources by name or description."""
        query = select(LawSource).where(
            or_(
                LawSource.name.ilike(f"%{search_term}%"),
                LawSource.description.ilike(f"%{search_term}%")
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_law_source(self, source_id: int, **kwargs) -> Optional[LawSource]:
        """Update law source fields."""
        source = await self.get_law_source_by_id(source_id)
        if not source:
            return None
        
        for key, value in kwargs.items():
            if hasattr(source, key) and value is not None:
                setattr(source, key, value)
        
        await self.db.commit()
        await self.db.refresh(source)
        logger.info(f"Updated law source {source_id}")
        return source

    async def delete_law_source(self, source_id: int) -> bool:
        """Delete law source and all its articles."""
        source = await self.get_law_source_by_id(source_id)
        if not source:
            return False
        
        await self.db.delete(source)
        await self.db.commit()
        logger.info(f"Deleted law source {source_id}")
        return True

    async def get_branches_by_source_id(self, source_id: int) -> List:
        """Get all branches (chapters) for a law source."""
        from ..models.legal_knowledge import LawBranch
        
        query = select(LawBranch).where(
            LawBranch.law_source_id == source_id
        ).order_by(LawBranch.order_index)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_chapters_by_branch_id(self, branch_id: int) -> List:
        """Get all chapters (sections) for a branch."""
        from ..models.legal_knowledge import LawChapter
        
        query = select(LawChapter).where(
            LawChapter.branch_id == branch_id
        ).order_by(LawChapter.order_index)
        
        result = await self.db.execute(query)
        return result.scalars().all()


class LawArticleRepository:
    """Repository for law articles operations."""

    def __init__(self, db: AsyncSession):
        """Initialize law article repository."""
        self.db = db

    async def create_law_article(
        self,
        law_source_id: int,
        content: str,
        article_number: Optional[str] = None,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None
    ) -> LawArticle:
        """Create a new law article."""
        article = LawArticle(
            law_source_id=law_source_id,
            article_number=article_number,
            title=title,
            content=content,
            keywords=keywords or [],
            embedding=json.dumps(embedding) if embedding else None
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        logger.info(f"Created law article {article.id}")
        return article

    async def get_article_by_id(self, article_id: int) -> Optional[LawArticle]:
        """Get law article by ID with law source preloaded."""
        result = await self.db.execute(
            select(LawArticle)
            .options(selectinload(LawArticle.law_source))
            .where(LawArticle.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_articles_by_source(
        self,
        law_source_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawArticle]:
        """Get articles for a specific law source."""
        result = await self.db.execute(
            select(LawArticle)
            .where(LawArticle.law_source_id == law_source_id)
            .order_by(LawArticle.article_number)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_articles(
        self,
        search_term: str,
        law_source_id: Optional[int] = None,
        limit: int = 50
    ) -> List[LawArticle]:
        """Search articles by content or title."""
        query = select(LawArticle).where(
            or_(
                LawArticle.content.ilike(f"%{search_term}%"),
                LawArticle.title.ilike(f"%{search_term}%")
            )
        )
        
        if law_source_id:
            query = query.where(LawArticle.law_source_id == law_source_id)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_article_embedding(
        self,
        article_id: int,
        embedding: List[float]
    ) -> Optional[LawArticle]:
        """Update article embedding vector."""
        article = await self.get_article_by_id(article_id)
        if not article:
            return None
        
        article.embedding = json.dumps(embedding)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def get_by_chapter_id(self, chapter_id: int) -> List:
        """Get all articles for a specific chapter."""
        query = select(LawArticle).where(
            LawArticle.chapter_id == chapter_id
        ).order_by(LawArticle.order_index)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_branch_id(self, branch_id: int) -> List:
        """Get all articles for a specific branch (not in any chapter)."""
        query = select(LawArticle).where(
            and_(
                LawArticle.branch_id == branch_id,
                LawArticle.chapter_id.is_(None)
            )
        ).order_by(LawArticle.order_index)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_orphaned_articles(self, law_source_id: int) -> List:
        """Get articles that are not in any branch or chapter."""
        query = select(LawArticle).where(
            and_(
                LawArticle.law_source_id == law_source_id,
                LawArticle.branch_id.is_(None),
                LawArticle.chapter_id.is_(None)
            )
        ).order_by(LawArticle.order_index)
        
        result = await self.db.execute(query)
        return result.scalars().all()


class LegalCaseRepository:
    """Repository for legal cases operations."""

    def __init__(self, db: AsyncSession):
        """Initialize legal case repository."""
        self.db = db

    async def create_legal_case(
        self,
        title: str,
        case_number: Optional[str] = None,
        description: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        court_name: Optional[str] = None,
        decision_date: Optional[str] = None,
        involved_parties: Optional[str] = None,
        pdf_path: Optional[str] = None,
        source_reference: Optional[str] = None,
        case_type: Optional[str] = None,
        court_level: Optional[str] = None,
        case_outcome: Optional[str] = None,
        judge_names: Optional[List[str]] = None,
        claim_amount: Optional[float] = None
    ) -> LegalCase:
        """Create a new legal case."""
        case = LegalCase(
            case_number=case_number,
            title=title,
            description=description,
            jurisdiction=jurisdiction,
            court_name=court_name,
            decision_date=decision_date,
            involved_parties=involved_parties,
            pdf_path=pdf_path,
            source_reference=source_reference,
            case_type=case_type,
            court_level=court_level,
            case_outcome=case_outcome,
            judge_names=judge_names or [],
            claim_amount=claim_amount
        )
        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)
        logger.info(f"Created legal case {case.id}: {title}")
        return case

    async def get_case_by_id(self, case_id: int) -> Optional[LegalCase]:
        """Get legal case by ID with sections preloaded."""
        result = await self.db.execute(
            select(LegalCase)
            .options(selectinload(LegalCase.sections))
            .where(LegalCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_cases(
        self,
        skip: int = 0,
        limit: int = 100,
        jurisdiction: Optional[str] = None,
        court_name: Optional[str] = None,
        case_type: Optional[str] = None,
        court_level: Optional[str] = None,
        case_outcome: Optional[str] = None
    ) -> Tuple[List[LegalCase], int]:
        """Get legal cases with filtering and pagination."""
        query = select(LegalCase)
        count_query = select(func.count()).select_from(LegalCase)
        
        filters = []
        if jurisdiction:
            filters.append(LegalCase.jurisdiction == jurisdiction)
        if court_name:
            filters.append(LegalCase.court_name == court_name)
        if case_type:
            filters.append(LegalCase.case_type == case_type)
        if court_level:
            filters.append(LegalCase.court_level == court_level)
        if case_outcome:
            filters.append(LegalCase.case_outcome == case_outcome)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get cases with pagination
        query = query.order_by(desc(LegalCase.decision_date)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        cases = result.scalars().all()
        
        return cases, total

    async def search_cases(self, search_term: str, limit: int = 50) -> List[LegalCase]:
        """Search legal cases by title, description, or case number."""
        query = select(LegalCase).where(
            or_(
                LegalCase.title.ilike(f"%{search_term}%"),
                LegalCase.description.ilike(f"%{search_term}%"),
                LegalCase.case_number.ilike(f"%{search_term}%"),
                LegalCase.case_type.ilike(f"%{search_term}%"),
                LegalCase.court_level.ilike(f"%{search_term}%"),
                LegalCase.case_outcome.ilike(f"%{search_term}%")
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_cases_by_type(self, case_type: str, limit: int = 100) -> List[LegalCase]:
        """Get cases by case type."""
        result = await self.db.execute(
            select(LegalCase)
            .where(LegalCase.case_type == case_type)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_cases_by_court_level(self, court_level: str, limit: int = 100) -> List[LegalCase]:
        """Get cases by court level."""
        result = await self.db.execute(
            select(LegalCase)
            .where(LegalCase.court_level == court_level)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_cases_by_outcome(self, case_outcome: str, limit: int = 100) -> List[LegalCase]:
        """Get cases by case outcome."""
        result = await self.db.execute(
            select(LegalCase)
            .where(LegalCase.case_outcome == case_outcome)
            .limit(limit)
        )
        return result.scalars().all()


class CaseSectionRepository:
    """Repository for case sections operations."""

    def __init__(self, db: AsyncSession):
        """Initialize case section repository."""
        self.db = db

    async def create_case_section(
        self,
        case_id: int,
        content: str,
        section_type: str,
        embedding: Optional[List[float]] = None
    ) -> CaseSection:
        """Create a new case section."""
        section = CaseSection(
            case_id=case_id,
            section_type=section_type,
            content=content,
            embedding=json.dumps(embedding) if embedding else None
        )
        self.db.add(section)
        await self.db.commit()
        await self.db.refresh(section)
        return section

    async def get_sections_by_case(
        self,
        case_id: int,
        section_type: Optional[str] = None
    ) -> List[CaseSection]:
        """Get sections for a specific case."""
        query = select(CaseSection).where(CaseSection.case_id == case_id)
        
        if section_type:
            query = query.where(CaseSection.section_type == section_type)
        
        query = query.order_by(CaseSection.id)
        result = await self.db.execute(query)
        return result.scalars().all()


class LegalTermRepository:
    """Repository for legal terms operations."""

    def __init__(self, db: AsyncSession):
        """Initialize legal term repository."""
        self.db = db

    async def create_legal_term(
        self,
        term: str,
        definition: Optional[str] = None,
        source: Optional[str] = None,
        related_terms: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None
    ) -> LegalTerm:
        """Create a new legal term."""
        legal_term = LegalTerm(
            term=term,
            definition=definition,
            source=source,
            related_terms=related_terms or [],
            embedding=json.dumps(embedding) if embedding else None
        )
        self.db.add(legal_term)
        await self.db.commit()
        await self.db.refresh(legal_term)
        logger.info(f"Created legal term {legal_term.id}: {term}")
        return legal_term

    async def get_term_by_id(self, term_id: int) -> Optional[LegalTerm]:
        """Get legal term by ID."""
        result = await self.db.execute(
            select(LegalTerm).where(LegalTerm.id == term_id)
        )
        return result.scalar_one_or_none()

    async def search_terms(self, search_term: str, limit: int = 50) -> List[LegalTerm]:
        """Search legal terms by term or definition."""
        query = select(LegalTerm).where(
            or_(
                LegalTerm.term.ilike(f"%{search_term}%"),
                LegalTerm.definition.ilike(f"%{search_term}%")
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_terms_by_source(self, source: str, limit: int = 100) -> List[LegalTerm]:
        """Get terms from a specific source."""
        result = await self.db.execute(
            select(LegalTerm)
            .where(LegalTerm.source == source)
            .limit(limit)
        )
        return result.scalars().all()


class KnowledgeDocumentRepository:
    """Repository for knowledge documents operations."""

    def __init__(self, db: AsyncSession):
        """Initialize knowledge document repository."""
        self.db = db

    async def create_knowledge_document(
        self,
        title: str,
        category: str,
        file_path: Optional[str] = None,
        source_type: str = "uploaded",
        uploaded_by: Optional[int] = None,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeDocument:
        """Create a new knowledge document."""
        document = KnowledgeDocument(
            title=title,
            category=category,
            file_path=file_path,
            source_type=source_type,
            status="raw",
            uploaded_by=uploaded_by,
            document_metadata=document_metadata or {}
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        logger.info(f"Created knowledge document {document.id}: {title}")
        return document

    async def get_document_by_id(self, document_id: int) -> Optional[KnowledgeDocument]:
        """Get knowledge document by ID with chunks preloaded."""
        result = await self.db.execute(
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        uploaded_by: Optional[int] = None
    ) -> Tuple[List[KnowledgeDocument], int]:
        """Get knowledge documents with filtering and pagination."""
        query = select(KnowledgeDocument)
        count_query = select(func.count()).select_from(KnowledgeDocument)
        
        filters = []
        if category:
            filters.append(KnowledgeDocument.category == category)
        if status:
            filters.append(KnowledgeDocument.status == status)
        if uploaded_by:
            filters.append(KnowledgeDocument.uploaded_by == uploaded_by)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get documents with pagination
        query = query.order_by(desc(KnowledgeDocument.uploaded_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return documents, total

    async def update_document_status(
        self,
        document_id: int,
        status: str,
        processed_at: Optional[datetime] = None
    ) -> Optional[KnowledgeDocument]:
        """Update document processing status."""
        document = await self.get_document_by_id(document_id)
        if not document:
            return None
        
        document.status = status
        if processed_at:
            document.processed_at = processed_at
        
        await self.db.commit()
        await self.db.refresh(document)
        logger.info(f"Updated document {document_id} status to {status}")
        return document


class KnowledgeChunkRepository:
    """Repository for knowledge chunks operations."""

    def __init__(self, db: AsyncSession):
        """Initialize knowledge chunk repository."""
        self.db = db

    async def create_knowledge_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        tokens_count: Optional[int] = None,
        embedding: Optional[List[float]] = None,
        law_source_ref: Optional[int] = None,
        case_ref: Optional[int] = None,
        term_ref: Optional[int] = None
    ) -> KnowledgeChunk:
        """Create a new knowledge chunk."""
        chunk = KnowledgeChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            tokens_count=tokens_count,
            embedding=json.dumps(embedding) if embedding else None,
            law_source_ref=law_source_ref,
            case_ref=case_ref,
            term_ref=term_ref
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def get_chunks_by_document(
        self,
        document_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[KnowledgeChunk]:
        """Get chunks for a specific document."""
        result = await self.db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_chunks(
        self,
        search_term: str,
        document_category: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeChunk]:
        """Search chunks by content."""
        query = select(KnowledgeChunk).join(KnowledgeDocument).where(
            KnowledgeChunk.content.ilike(f"%{search_term}%")
        )
        
        if document_category:
            query = query.where(KnowledgeDocument.category == document_category)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()


class AnalysisResultRepository:
    """Repository for analysis results operations."""

    def __init__(self, db: AsyncSession):
        """Initialize analysis result repository."""
        self.db = db

    async def create_analysis_result(
        self,
        document_id: int,
        analysis_type: str,
        output: Dict[str, Any],
        model_version: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> AnalysisResult:
        """Create a new analysis result."""
        result = AnalysisResult(
            document_id=document_id,
            analysis_type=analysis_type,
            model_version=model_version,
            output=output,
            confidence=confidence
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        logger.info(f"Created analysis result {result.id}")
        return result

    async def get_results_by_document(
        self,
        document_id: int,
        analysis_type: Optional[str] = None
    ) -> List[AnalysisResult]:
        """Get analysis results for a specific document."""
        query = select(AnalysisResult).where(AnalysisResult.document_id == document_id)
        
        if analysis_type:
            query = query.where(AnalysisResult.analysis_type == analysis_type)
        
        query = query.order_by(desc(AnalysisResult.created_at))
        result = await self.db.execute(query)
        return result.scalars().all()


class KnowledgeLinkRepository:
    """Repository for knowledge links operations."""

    def __init__(self, db: AsyncSession):
        """Initialize knowledge link repository."""
        self.db = db

    async def create_knowledge_link(
        self,
        source_type: str,
        source_id: int,
        target_type: str,
        target_id: int,
        relation: str,
        weight: float = 1.0
    ) -> KnowledgeLink:
        """Create a new knowledge link."""
        link = KnowledgeLink(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relation=relation,
            weight=weight
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_links_by_source(
        self,
        source_type: str,
        source_id: int
    ) -> List[KnowledgeLink]:
        """Get links from a specific source."""
        result = await self.db.execute(
            select(KnowledgeLink)
            .where(
                and_(
                    KnowledgeLink.source_type == source_type,
                    KnowledgeLink.source_id == source_id
                )
            )
        )
        return result.scalars().all()

    async def get_links_by_target(
        self,
        target_type: str,
        target_id: int
    ) -> List[KnowledgeLink]:
        """Get links to a specific target."""
        result = await self.db.execute(
            select(KnowledgeLink)
            .where(
                and_(
                    KnowledgeLink.target_type == target_type,
                    KnowledgeLink.target_id == target_id
                )
            )
        )
        return result.scalars().all()


class KnowledgeMetadataRepository:
    """Repository for knowledge metadata operations."""

    def __init__(self, db: AsyncSession):
        """Initialize knowledge metadata repository."""
        self.db = db

    async def create_metadata(
        self,
        object_type: str,
        object_id: int,
        key: str,
        value: Optional[str] = None
    ) -> KnowledgeMetadata:
        """Create new metadata entry."""
        metadata = KnowledgeMetadata(
            object_type=object_type,
            object_id=object_id,
            key=key,
            value=value
        )
        self.db.add(metadata)
        await self.db.commit()
        await self.db.refresh(metadata)
        return metadata

    async def get_metadata_by_object(
        self,
        object_type: str,
        object_id: int
    ) -> List[KnowledgeMetadata]:
        """Get all metadata for a specific object."""
        result = await self.db.execute(
            select(KnowledgeMetadata)
            .where(
                and_(
                    KnowledgeMetadata.object_type == object_type,
                    KnowledgeMetadata.object_id == object_id
                )
            )
        )
        return result.scalars().all()

    async def get_metadata_value(
        self,
        object_type: str,
        object_id: int,
        key: str
    ) -> Optional[str]:
        """Get specific metadata value."""
        result = await self.db.execute(
            select(KnowledgeMetadata.value)
            .where(
                and_(
                    KnowledgeMetadata.object_type == object_type,
                    KnowledgeMetadata.object_id == object_id,
                    KnowledgeMetadata.key == key
                )
            )
        )
        return result.scalar_one_or_none()

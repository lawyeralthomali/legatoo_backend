"""
Legal Hierarchy Repository

This module handles database operations for legal hierarchy:
- Law Branches (الأبواب)
- Law Chapters (الفصول)
- Law Articles (المواد)
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime

from ..models.legal_knowledge import (
    LawBranch, LawChapter, LawArticle, LawSource
)

logger = logging.getLogger(__name__)


class LegalHierarchyRepository:
    """Repository for legal hierarchy CRUD operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    # =====================================================
    # LAW BRANCH OPERATIONS
    # =====================================================

    async def create_branch(
        self,
        law_source_id: int,
        branch_number: Optional[str],
        branch_name: str,
        description: Optional[str] = None,
        order_index: int = 0,
        source_document_id: Optional[int] = None
    ) -> LawBranch:
        """Create a new law branch."""
        branch = LawBranch(
            law_source_id=law_source_id,
            branch_number=branch_number,
            branch_name=branch_name,
            description=description,
            order_index=order_index,
            source_document_id=source_document_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(branch)
        await self.db.flush()
        await self.db.refresh(branch)
        
        logger.info(f"Created branch {branch.id}: {branch.branch_name}")
        return branch

    async def get_branch_by_id(self, branch_id: int) -> Optional[LawBranch]:
        """Get branch by ID with related data."""
        query = (
            select(LawBranch)
            .where(LawBranch.id == branch_id)
            .options(selectinload(LawBranch.chapters))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_branches_by_law_source(
        self,
        law_source_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawBranch]:
        """Get all branches for a law source."""
        query = (
            select(LawBranch)
            .where(LawBranch.law_source_id == law_source_id)
            .order_by(LawBranch.order_index, LawBranch.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_branch(
        self,
        branch_id: int,
        **kwargs
    ) -> Optional[LawBranch]:
        """Update branch fields."""
        branch = await self.get_branch_by_id(branch_id)
        
        if not branch:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'branch_number', 'branch_name', 'description', 'order_index'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(branch, field, value)
        
        branch.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(branch)
        
        logger.info(f"Updated branch {branch.id}")
        return branch

    async def delete_branch(self, branch_id: int) -> bool:
        """Delete branch and cascade to chapters and articles."""
        branch = await self.get_branch_by_id(branch_id)
        
        if not branch:
            return False
        
        await self.db.delete(branch)
        await self.db.flush()
        
        logger.info(f"Deleted branch {branch_id}")
        return True

    async def count_branches_by_law_source(self, law_source_id: int) -> int:
        """Count branches for a law source."""
        query = select(func.count()).select_from(LawBranch).where(
            LawBranch.law_source_id == law_source_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # =====================================================
    # LAW CHAPTER OPERATIONS
    # =====================================================

    async def create_chapter(
        self,
        branch_id: int,
        chapter_number: Optional[str],
        chapter_name: str,
        description: Optional[str] = None,
        order_index: int = 0,
        source_document_id: Optional[int] = None
    ) -> LawChapter:
        """Create a new law chapter."""
        chapter = LawChapter(
            branch_id=branch_id,
            chapter_number=chapter_number,
            chapter_name=chapter_name,
            description=description,
            order_index=order_index,
            source_document_id=source_document_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(chapter)
        await self.db.flush()
        await self.db.refresh(chapter)
        
        logger.info(f"Created chapter {chapter.id}: {chapter.chapter_name}")
        return chapter

    async def get_chapter_by_id(self, chapter_id: int) -> Optional[LawChapter]:
        """Get chapter by ID with related data."""
        query = (
            select(LawChapter)
            .where(LawChapter.id == chapter_id)
            .options(selectinload(LawChapter.articles))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_chapters_by_branch(
        self,
        branch_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawChapter]:
        """Get all chapters for a branch."""
        query = (
            select(LawChapter)
            .where(LawChapter.branch_id == branch_id)
            .order_by(LawChapter.order_index, LawChapter.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_chapter(
        self,
        chapter_id: int,
        **kwargs
    ) -> Optional[LawChapter]:
        """Update chapter fields."""
        chapter = await self.get_chapter_by_id(chapter_id)
        
        if not chapter:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'chapter_number', 'chapter_name', 'description', 'order_index'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(chapter, field, value)
        
        chapter.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(chapter)
        
        logger.info(f"Updated chapter {chapter.id}")
        return chapter

    async def delete_chapter(self, chapter_id: int) -> bool:
        """Delete chapter and cascade to articles."""
        chapter = await self.get_chapter_by_id(chapter_id)
        
        if not chapter:
            return False
        
        await self.db.delete(chapter)
        await self.db.flush()
        
        logger.info(f"Deleted chapter {chapter_id}")
        return True

    async def count_chapters_by_branch(self, branch_id: int) -> int:
        """Count chapters for a branch."""
        query = select(func.count()).select_from(LawChapter).where(
            LawChapter.branch_id == branch_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # =====================================================
    # LAW ARTICLE OPERATIONS
    # =====================================================

    async def create_article(
        self,
        law_source_id: int,
        article_number: Optional[str],
        title: Optional[str],
        content: str,
        branch_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        keywords: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        order_index: int = 0,
        source_document_id: Optional[int] = None
    ) -> LawArticle:
        """Create a new law article."""
        article = LawArticle(
            law_source_id=law_source_id,
            branch_id=branch_id,
            chapter_id=chapter_id,
            article_number=article_number,
            title=title,
            content=content,
            keywords=keywords or [],
            embedding=embedding,
            order_index=order_index,
            source_document_id=source_document_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(article)
        await self.db.flush()
        await self.db.refresh(article)
        
        logger.info(f"Created article {article.id}: {article.article_number}")
        return article

    async def get_article_by_id(self, article_id: int) -> Optional[LawArticle]:
        """Get article by ID with related data."""
        query = (
            select(LawArticle)
            .where(LawArticle.id == article_id)
            .options(
                selectinload(LawArticle.law_source),
                selectinload(LawArticle.branch),
                selectinload(LawArticle.chapter)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_articles_by_law_source(
        self,
        law_source_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawArticle]:
        """Get all articles for a law source."""
        query = (
            select(LawArticle)
            .where(LawArticle.law_source_id == law_source_id)
            .order_by(LawArticle.order_index, LawArticle.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_articles_by_branch(
        self,
        branch_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawArticle]:
        """Get all articles for a branch."""
        query = (
            select(LawArticle)
            .where(LawArticle.branch_id == branch_id)
            .order_by(LawArticle.order_index, LawArticle.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_articles_by_chapter(
        self,
        chapter_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawArticle]:
        """Get all articles for a chapter."""
        query = (
            select(LawArticle)
            .where(LawArticle.chapter_id == chapter_id)
            .order_by(LawArticle.order_index, LawArticle.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_articles(
        self,
        law_source_id: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LawArticle]:
        """Search articles by content or keywords."""
        query = select(LawArticle)
        
        conditions = []
        
        if law_source_id:
            conditions.append(LawArticle.law_source_id == law_source_id)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            conditions.append(
                or_(
                    LawArticle.content.ilike(search_pattern),
                    LawArticle.title.ilike(search_pattern),
                    LawArticle.article_number.ilike(search_pattern)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(LawArticle.order_index, LawArticle.id).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_article(
        self,
        article_id: int,
        **kwargs
    ) -> Optional[LawArticle]:
        """Update article fields."""
        article = await self.get_article_by_id(article_id)
        
        if not article:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'article_number', 'title', 'content', 'keywords', 
            'embedding', 'branch_id', 'chapter_id', 'order_index'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(article, field, value)
        
        article.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(article)
        
        logger.info(f"Updated article {article.id}")
        return article

    async def delete_article(self, article_id: int) -> bool:
        """Delete article."""
        article = await self.get_article_by_id(article_id)
        
        if not article:
            return False
        
        await self.db.delete(article)
        await self.db.flush()
        
        logger.info(f"Deleted article {article_id}")
        return True

    async def count_articles_by_law_source(self, law_source_id: int) -> int:
        """Count articles for a law source."""
        query = select(func.count()).select_from(LawArticle).where(
            LawArticle.law_source_id == law_source_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_articles_by_branch(self, branch_id: int) -> int:
        """Count articles for a branch."""
        query = select(func.count()).select_from(LawArticle).where(
            LawArticle.branch_id == branch_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_articles_by_chapter(self, chapter_id: int) -> int:
        """Count articles for a chapter."""
        query = select(func.count()).select_from(LawArticle).where(
            LawArticle.chapter_id == chapter_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # =====================================================
    # BATCH OPERATIONS
    # =====================================================

    async def reorder_branches(
        self,
        law_source_id: int,
        branch_order: List[Dict[str, int]]
    ) -> bool:
        """Reorder branches for a law source.
        
        Args:
            law_source_id: Law source ID
            branch_order: List of dicts with 'id' and 'order_index'
        """
        try:
            for item in branch_order:
                branch = await self.get_branch_by_id(item['id'])
                if branch and branch.law_source_id == law_source_id:
                    branch.order_index = item['order_index']
                    branch.updated_at = datetime.utcnow()
            
            await self.db.flush()
            logger.info(f"Reordered {len(branch_order)} branches for law source {law_source_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reorder branches: {str(e)}")
            return False

    async def reorder_chapters(
        self,
        branch_id: int,
        chapter_order: List[Dict[str, int]]
    ) -> bool:
        """Reorder chapters for a branch."""
        try:
            for item in chapter_order:
                chapter = await self.get_chapter_by_id(item['id'])
                if chapter and chapter.branch_id == branch_id:
                    chapter.order_index = item['order_index']
                    chapter.updated_at = datetime.utcnow()
            
            await self.db.flush()
            logger.info(f"Reordered {len(chapter_order)} chapters for branch {branch_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reorder chapters: {str(e)}")
            return False

    async def reorder_articles(
        self,
        parent_id: int,
        parent_type: str,  # 'branch' or 'chapter'
        article_order: List[Dict[str, int]]
    ) -> bool:
        """Reorder articles for a branch or chapter."""
        try:
            for item in article_order:
                article = await self.get_article_by_id(item['id'])
                if article:
                    if parent_type == 'branch' and article.branch_id == parent_id:
                        article.order_index = item['order_index']
                        article.updated_at = datetime.utcnow()
                    elif parent_type == 'chapter' and article.chapter_id == parent_id:
                        article.order_index = item['order_index']
                        article.updated_at = datetime.utcnow()
            
            await self.db.flush()
            logger.info(f"Reordered {len(article_order)} articles for {parent_type} {parent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reorder articles: {str(e)}")
            return False

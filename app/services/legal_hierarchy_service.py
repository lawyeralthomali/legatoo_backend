"""
Legal Hierarchy Service

This service handles business logic for legal hierarchy:
- Law Branches (الأبواب)
- Law Chapters (الفصول)
- Law Articles (المواد)
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.legal_hierarchy_repository import LegalHierarchyRepository
from ..schemas.legal_knowledge import (
    LawBranchCreate, LawBranchUpdate, LawBranchResponse,
    LawChapterCreate, LawChapterUpdate, LawChapterResponse,
    LawArticleCreate, LawArticleUpdate, LawArticleResponse
)

logger = logging.getLogger(__name__)


class LegalHierarchyService:
    """Service for legal hierarchy business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.repo = LegalHierarchyRepository(db)

    # =====================================================
    # BRANCH OPERATIONS
    # =====================================================

    async def create_branch(
        self,
        branch_data: LawBranchCreate,
        current_user_id: int
    ) -> Dict[str, Any]:
        """Create a new law branch."""
        try:
            # Verify law source exists
            # (Could add validation here)
            
            branch = await self.repo.create_branch(
                law_source_id=branch_data.law_source_id,
                branch_number=branch_data.branch_number,
                branch_name=branch_data.branch_name,
                description=branch_data.description,
                order_index=branch_data.order_index
            )
            
            await self.db.commit()
            
            # Get chapter count
            chapters_count = await self.repo.count_chapters_by_branch(branch.id)
            
            return {
                "success": True,
                "message": "Branch created successfully",
                "data": {
                    "id": branch.id,
                    "law_source_id": branch.law_source_id,
                    "branch_number": branch.branch_number,
                    "branch_name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters_count": chapters_count,
                    "created_at": branch.created_at,
                    "updated_at": branch.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create branch: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create branch: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_branch(self, branch_id: int) -> Dict[str, Any]:
        """Get branch by ID."""
        try:
            branch = await self.repo.get_branch_by_id(branch_id)
            
            if not branch:
                return {
                    "success": False,
                    "message": "Branch not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Branch not found"}]
                }
            
            # Get chapters count
            chapters_count = await self.repo.count_chapters_by_branch(branch.id)
            
            # Get chapters
            chapters = await self.repo.get_chapters_by_branch(branch.id)
            
            return {
                "success": True,
                "message": "Branch retrieved successfully",
                "data": {
                    "id": branch.id,
                    "law_source_id": branch.law_source_id,
                    "branch_number": branch.branch_number,
                    "branch_name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters_count": chapters_count,
                    "chapters": [
                        {
                            "id": ch.id,
                            "chapter_number": ch.chapter_number,
                            "chapter_name": ch.chapter_name,
                            "description": ch.description,
                            "order_index": ch.order_index
                        }
                        for ch in chapters
                    ],
                    "created_at": branch.created_at,
                    "updated_at": branch.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get branch: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get branch: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_branches_by_law_source(
        self,
        law_source_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get all branches for a law source."""
        try:
            branches = await self.repo.get_branches_by_law_source(
                law_source_id, skip, limit
            )
            
            total_count = await self.repo.count_branches_by_law_source(law_source_id)
            
            branches_data = []
            for branch in branches:
                chapters_count = await self.repo.count_chapters_by_branch(branch.id)
                branches_data.append({
                    "id": branch.id,
                    "law_source_id": branch.law_source_id,
                    "branch_number": branch.branch_number,
                    "branch_name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters_count": chapters_count,
                    "created_at": branch.created_at,
                    "updated_at": branch.updated_at
                })
            
            return {
                "success": True,
                "message": f"Retrieved {len(branches)} branches",
                "data": {
                    "branches": branches_data,
                    "total": total_count,
                    "skip": skip,
                    "limit": limit
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get branches: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get branches: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def update_branch(
        self,
        branch_id: int,
        branch_data: LawBranchUpdate
    ) -> Dict[str, Any]:
        """Update branch."""
        try:
            # Convert Pydantic model to dict, excluding None values
            update_data = branch_data.model_dump(exclude_none=True)
            
            branch = await self.repo.update_branch(branch_id, **update_data)
            
            if not branch:
                return {
                    "success": False,
                    "message": "Branch not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Branch not found"}]
                }
            
            await self.db.commit()
            
            chapters_count = await self.repo.count_chapters_by_branch(branch.id)
            
            return {
                "success": True,
                "message": "Branch updated successfully",
                "data": {
                    "id": branch.id,
                    "law_source_id": branch.law_source_id,
                    "branch_number": branch.branch_number,
                    "branch_name": branch.branch_name,
                    "description": branch.description,
                    "order_index": branch.order_index,
                    "chapters_count": chapters_count,
                    "created_at": branch.created_at,
                    "updated_at": branch.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update branch: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update branch: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def delete_branch(self, branch_id: int) -> Dict[str, Any]:
        """Delete branch and cascade to chapters and articles."""
        try:
            success = await self.repo.delete_branch(branch_id)
            
            if not success:
                return {
                    "success": False,
                    "message": "Branch not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Branch not found"}]
                }
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Branch deleted successfully",
                "data": {"id": branch_id, "deleted": True},
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete branch: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete branch: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    # =====================================================
    # CHAPTER OPERATIONS
    # =====================================================

    async def create_chapter(
        self,
        chapter_data: LawChapterCreate,
        current_user_id: int
    ) -> Dict[str, Any]:
        """Create a new law chapter."""
        try:
            chapter = await self.repo.create_chapter(
                branch_id=chapter_data.branch_id,
                chapter_number=chapter_data.chapter_number,
                chapter_name=chapter_data.chapter_name,
                description=chapter_data.description,
                order_index=chapter_data.order_index
            )
            
            await self.db.commit()
            
            articles_count = await self.repo.count_articles_by_chapter(chapter.id)
            
            return {
                "success": True,
                "message": "Chapter created successfully",
                "data": {
                    "id": chapter.id,
                    "branch_id": chapter.branch_id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_name": chapter.chapter_name,
                    "description": chapter.description,
                    "order_index": chapter.order_index,
                    "articles_count": articles_count,
                    "created_at": chapter.created_at,
                    "updated_at": chapter.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create chapter: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create chapter: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_chapter(self, chapter_id: int) -> Dict[str, Any]:
        """Get chapter by ID."""
        try:
            chapter = await self.repo.get_chapter_by_id(chapter_id)
            
            if not chapter:
                return {
                    "success": False,
                    "message": "Chapter not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Chapter not found"}]
                }
            
            articles_count = await self.repo.count_articles_by_chapter(chapter.id)
            articles = await self.repo.get_articles_by_chapter(chapter.id)
            
            return {
                "success": True,
                "message": "Chapter retrieved successfully",
                "data": {
                    "id": chapter.id,
                    "branch_id": chapter.branch_id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_name": chapter.chapter_name,
                    "description": chapter.description,
                    "order_index": chapter.order_index,
                    "articles_count": articles_count,
                    "articles": [
                        {
                            "id": art.id,
                            "article_number": art.article_number,
                            "title": art.title,
                            "content": art.content[:200] + "..." if len(art.content) > 200 else art.content,
                            "order_index": art.order_index
                        }
                        for art in articles
                    ],
                    "created_at": chapter.created_at,
                    "updated_at": chapter.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get chapter: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get chapter: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_chapters_by_branch(
        self,
        branch_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get all chapters for a branch."""
        try:
            chapters = await self.repo.get_chapters_by_branch(
                branch_id, skip, limit
            )
            
            total_count = await self.repo.count_chapters_by_branch(branch_id)
            
            chapters_data = []
            for chapter in chapters:
                articles_count = await self.repo.count_articles_by_chapter(chapter.id)
                chapters_data.append({
                    "id": chapter.id,
                    "branch_id": chapter.branch_id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_name": chapter.chapter_name,
                    "description": chapter.description,
                    "order_index": chapter.order_index,
                    "articles_count": articles_count,
                    "created_at": chapter.created_at,
                    "updated_at": chapter.updated_at
                })
            
            return {
                "success": True,
                "message": f"Retrieved {len(chapters)} chapters",
                "data": {
                    "chapters": chapters_data,
                    "total": total_count,
                    "skip": skip,
                    "limit": limit
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get chapters: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get chapters: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def update_chapter(
        self,
        chapter_id: int,
        chapter_data: LawChapterUpdate
    ) -> Dict[str, Any]:
        """Update chapter."""
        try:
            update_data = chapter_data.model_dump(exclude_none=True)
            
            chapter = await self.repo.update_chapter(chapter_id, **update_data)
            
            if not chapter:
                return {
                    "success": False,
                    "message": "Chapter not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Chapter not found"}]
                }
            
            await self.db.commit()
            
            articles_count = await self.repo.count_articles_by_chapter(chapter.id)
            
            return {
                "success": True,
                "message": "Chapter updated successfully",
                "data": {
                    "id": chapter.id,
                    "branch_id": chapter.branch_id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_name": chapter.chapter_name,
                    "description": chapter.description,
                    "order_index": chapter.order_index,
                    "articles_count": articles_count,
                    "created_at": chapter.created_at,
                    "updated_at": chapter.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update chapter: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update chapter: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def delete_chapter(self, chapter_id: int) -> Dict[str, Any]:
        """Delete chapter and cascade to articles."""
        try:
            success = await self.repo.delete_chapter(chapter_id)
            
            if not success:
                return {
                    "success": False,
                    "message": "Chapter not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Chapter not found"}]
                }
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Chapter deleted successfully",
                "data": {"id": chapter_id, "deleted": True},
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete chapter: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete chapter: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    # =====================================================
    # ARTICLE OPERATIONS
    # =====================================================

    async def create_article(
        self,
        article_data: LawArticleCreate,
        current_user_id: int
    ) -> Dict[str, Any]:
        """Create a new law article."""
        try:
            article = await self.repo.create_article(
                law_source_id=article_data.law_source_id,
                branch_id=article_data.branch_id,
                chapter_id=article_data.chapter_id,
                article_number=article_data.article_number,
                title=article_data.title,
                content=article_data.content,
                keywords=article_data.keywords,
                embedding=article_data.embedding,
                order_index=article_data.order_index
            )
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Article created successfully",
                "data": {
                    "id": article.id,
                    "law_source_id": article.law_source_id,
                    "branch_id": article.branch_id,
                    "chapter_id": article.chapter_id,
                    "article_number": article.article_number,
                    "title": article.title,
                    "content": article.content,
                    "keywords": article.keywords,
                    "order_index": article.order_index,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create article: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create article: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_article(self, article_id: int) -> Dict[str, Any]:
        """Get article by ID."""
        try:
            article = await self.repo.get_article_by_id(article_id)
            
            if not article:
                return {
                    "success": False,
                    "message": "Article not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Article not found"}]
                }
            
            return {
                "success": True,
                "message": "Article retrieved successfully",
                "data": {
                    "id": article.id,
                    "law_source_id": article.law_source_id,
                    "branch_id": article.branch_id,
                    "chapter_id": article.chapter_id,
                    "article_number": article.article_number,
                    "title": article.title,
                    "content": article.content,
                    "keywords": article.keywords,
                    "order_index": article.order_index,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get article: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get article: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_articles(
        self,
        law_source_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get articles with filters."""
        try:
            if chapter_id:
                articles = await self.repo.get_articles_by_chapter(
                    chapter_id, skip, limit
                )
                total = await self.repo.count_articles_by_chapter(chapter_id)
            elif branch_id:
                articles = await self.repo.get_articles_by_branch(
                    branch_id, skip, limit
                )
                total = await self.repo.count_articles_by_branch(branch_id)
            elif law_source_id:
                if search_query:
                    articles = await self.repo.search_articles(
                        law_source_id, search_query, skip, limit
                    )
                    total = len(articles)  # Approximate
                else:
                    articles = await self.repo.get_articles_by_law_source(
                        law_source_id, skip, limit
                    )
                    total = await self.repo.count_articles_by_law_source(law_source_id)
            else:
                if search_query:
                    articles = await self.repo.search_articles(
                        None, search_query, skip, limit
                    )
                    total = len(articles)
                else:
                    return {
                        "success": False,
                        "message": "Please provide law_source_id, branch_id, or chapter_id",
                        "data": None,
                        "errors": [{"field": None, "message": "Missing filter parameters"}]
                    }
            
            articles_data = [
                {
                    "id": art.id,
                    "law_source_id": art.law_source_id,
                    "branch_id": art.branch_id,
                    "chapter_id": art.chapter_id,
                    "article_number": art.article_number,
                    "title": art.title,
                    "content": art.content[:300] + "..." if len(art.content) > 300 else art.content,
                    "keywords": art.keywords,
                    "order_index": art.order_index,
                    "created_at": art.created_at
                }
                for art in articles
            ]
            
            return {
                "success": True,
                "message": f"Retrieved {len(articles)} articles",
                "data": {
                    "articles": articles_data,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get articles: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get articles: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def update_article(
        self,
        article_id: int,
        article_data: LawArticleUpdate
    ) -> Dict[str, Any]:
        """Update article."""
        try:
            update_data = article_data.model_dump(exclude_none=True)
            
            article = await self.repo.update_article(article_id, **update_data)
            
            if not article:
                return {
                    "success": False,
                    "message": "Article not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Article not found"}]
                }
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Article updated successfully",
                "data": {
                    "id": article.id,
                    "law_source_id": article.law_source_id,
                    "branch_id": article.branch_id,
                    "chapter_id": article.chapter_id,
                    "article_number": article.article_number,
                    "title": article.title,
                    "content": article.content,
                    "keywords": article.keywords,
                    "order_index": article.order_index,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at
                },
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update article: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update article: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def delete_article(self, article_id: int) -> Dict[str, Any]:
        """Delete article."""
        try:
            success = await self.repo.delete_article(article_id)
            
            if not success:
                return {
                    "success": False,
                    "message": "Article not found",
                    "data": None,
                    "errors": [{"field": "id", "message": "Article not found"}]
                }
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Article deleted successfully",
                "data": {"id": article_id, "deleted": True},
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete article: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete article: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

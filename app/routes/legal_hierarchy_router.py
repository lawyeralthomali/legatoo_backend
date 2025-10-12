"""
Legal Hierarchy API Router

This module provides REST API endpoints for managing legal hierarchy:
- Law Branches (الأبواب): GET, POST, PUT, DELETE
- Law Chapters (الفصول): GET, POST, PUT, DELETE
- Law Articles (المواد): GET, POST, PUT, DELETE
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..utils.auth import get_current_user
from ..schemas.legal_knowledge import (
    LawBranchCreate, LawBranchUpdate, LawBranchResponse,
    LawChapterCreate, LawChapterUpdate, LawChapterResponse,
    LawArticleCreate, LawArticleUpdate, LawArticleResponse
)
from ..services.legal.knowledge.legal_hierarchy_service import LegalHierarchyService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/legal-hierarchy",
    tags=["Legal Hierarchy (CRUD)"]
)


# =====================================================
# BRANCH ENDPOINTS
# =====================================================

@router.post("/branches")
async def create_branch(
    branch_data: LawBranchCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new law branch (الباب)
    
    **Required fields:**
    - law_source_id: ID of the law source
    - branch_name: Name/title of the branch
    
    **Optional fields:**
    - branch_number: Branch number (e.g., "الباب الأول")
    - description: Description of the branch
    - order_index: Display order (default: 0)
    """
    service = LegalHierarchyService(db)
    result = await service.create_branch(branch_data, current_user.sub)
    return result


@router.get("/branches/{branch_id}")
async def get_branch(
    branch_id: int = Path(..., gt=0, description="Branch ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific branch by ID with all its chapters
    """
    service = LegalHierarchyService(db)
    result = await service.get_branch(branch_id)
    return result


@router.get("/law-sources/{law_source_id}/branches")
async def get_branches_by_law_source(
    law_source_id: int = Path(..., gt=0, description="Law Source ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all branches for a specific law source
    
    **Query Parameters:**
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 500)
    
    **Returns:**
    - List of branches with their chapter counts
    - Total count
    - Pagination info
    """
    service = LegalHierarchyService(db)
    result = await service.get_branches_by_law_source(law_source_id, skip, limit)
    return result


@router.put("/branches/{branch_id}")
async def update_branch(
    branch_id: int = Path(..., gt=0, description="Branch ID"),
    branch_data: LawBranchUpdate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a branch
    
    **All fields are optional:**
    - branch_number: Update branch number
    - branch_name: Update branch name
    - description: Update description
    - order_index: Update display order
    """
    service = LegalHierarchyService(db)
    result = await service.update_branch(branch_id, branch_data)
    return result


@router.delete("/branches/{branch_id}")
async def delete_branch(
    branch_id: int = Path(..., gt=0, description="Branch ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a branch (CASCADE deletes all chapters and articles)
    
    **⚠️ Warning:** This will permanently delete:
    - The branch
    - All chapters under this branch
    - All articles under this branch
    """
    service = LegalHierarchyService(db)
    result = await service.delete_branch(branch_id)
    return result


# =====================================================
# CHAPTER ENDPOINTS
# =====================================================

@router.post("/chapters")
async def create_chapter(
    chapter_data: LawChapterCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new law chapter (الفصل)
    
    **Required fields:**
    - branch_id: ID of the parent branch
    - chapter_name: Name/title of the chapter
    
    **Optional fields:**
    - chapter_number: Chapter number (e.g., "الفصل الأول")
    - description: Description of the chapter
    - order_index: Display order (default: 0)
    """
    service = LegalHierarchyService(db)
    result = await service.create_chapter(chapter_data, current_user.sub)
    return result


@router.get("/chapters/{chapter_id}")
async def get_chapter(
    chapter_id: int = Path(..., gt=0, description="Chapter ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific chapter by ID with all its articles
    """
    service = LegalHierarchyService(db)
    result = await service.get_chapter(chapter_id)
    return result


@router.get("/branches/{branch_id}/chapters")
async def get_chapters_by_branch(
    branch_id: int = Path(..., gt=0, description="Branch ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chapters for a specific branch
    
    **Query Parameters:**
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 500)
    
    **Returns:**
    - List of chapters with their article counts
    - Total count
    - Pagination info
    """
    service = LegalHierarchyService(db)
    result = await service.get_chapters_by_branch(branch_id, skip, limit)
    return result


@router.put("/chapters/{chapter_id}")
async def update_chapter(
    chapter_id: int = Path(..., gt=0, description="Chapter ID"),
    chapter_data: LawChapterUpdate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chapter
    
    **All fields are optional:**
    - chapter_number: Update chapter number
    - chapter_name: Update chapter name
    - description: Update description
    - order_index: Update display order
    """
    service = LegalHierarchyService(db)
    result = await service.update_chapter(chapter_id, chapter_data)
    return result


@router.delete("/chapters/{chapter_id}")
async def delete_chapter(
    chapter_id: int = Path(..., gt=0, description="Chapter ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chapter (CASCADE deletes all articles)
    
    **⚠️ Warning:** This will permanently delete:
    - The chapter
    - All articles under this chapter
    """
    service = LegalHierarchyService(db)
    result = await service.delete_chapter(chapter_id)
    return result


# =====================================================
# ARTICLE ENDPOINTS
# =====================================================

@router.post("/articles")
async def create_article(
    article_data: LawArticleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new law article (المادة)
    
    **Required fields:**
    - law_source_id: ID of the law source
    - content: Full text content of the article
    
    **Optional fields:**
    - article_number: Article number (e.g., "المادة الأولى")
    - title: Article title/heading
    - branch_id: ID of parent branch (if any)
    - chapter_id: ID of parent chapter (if any)
    - keywords: List of keywords/tags
    - embedding: Vector embedding for semantic search
    - order_index: Display order (default: 0)
    """
    service = LegalHierarchyService(db)
    result = await service.create_article(article_data, current_user.sub)
    return result


@router.get("/articles/{article_id}")
async def get_article(
    article_id: int = Path(..., gt=0, description="Article ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific article by ID
    
    **Returns:**
    - Full article details
    - Related law source, branch, and chapter (if linked)
    """
    service = LegalHierarchyService(db)
    result = await service.get_article(article_id)
    return result


@router.get("/articles")
async def get_articles(
    law_source_id: Optional[int] = Query(None, gt=0, description="Filter by law source"),
    branch_id: Optional[int] = Query(None, gt=0, description="Filter by branch"),
    chapter_id: Optional[int] = Query(None, gt=0, description="Filter by chapter"),
    search_query: Optional[str] = Query(None, min_length=1, max_length=500, description="Search in content/title"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get articles with flexible filtering
    
    **Query Parameters:**
    - law_source_id: Get all articles for a law source
    - branch_id: Get all articles for a branch
    - chapter_id: Get all articles for a chapter
    - search_query: Search in article content, title, and number
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 500)
    
    **Note:** At least one filter (law_source_id, branch_id, or chapter_id) is required
    
    **Returns:**
    - List of articles (content truncated to 300 chars)
    - Total count
    - Pagination info
    """
    service = LegalHierarchyService(db)
    result = await service.get_articles(
        law_source_id=law_source_id,
        branch_id=branch_id,
        chapter_id=chapter_id,
        search_query=search_query,
        skip=skip,
        limit=limit
    )
    return result


@router.get("/law-sources/{law_source_id}/articles")
async def get_articles_by_law_source(
    law_source_id: int = Path(..., gt=0, description="Law Source ID"),
    search_query: Optional[str] = Query(None, min_length=1, max_length=500, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all articles for a specific law source
    
    **Convenience endpoint** - Same as /articles?law_source_id=X
    """
    service = LegalHierarchyService(db)
    result = await service.get_articles(
        law_source_id=law_source_id,
        search_query=search_query,
        skip=skip,
        limit=limit
    )
    return result


@router.get("/branches/{branch_id}/articles")
async def get_articles_by_branch(
    branch_id: int = Path(..., gt=0, description="Branch ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all articles for a specific branch
    
    **Convenience endpoint** - Same as /articles?branch_id=X
    """
    service = LegalHierarchyService(db)
    result = await service.get_articles(
        branch_id=branch_id,
        skip=skip,
        limit=limit
    )
    return result


@router.get("/chapters/{chapter_id}/articles")
async def get_articles_by_chapter(
    chapter_id: int = Path(..., gt=0, description="Chapter ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all articles for a specific chapter
    
    **Convenience endpoint** - Same as /articles?chapter_id=X
    """
    service = LegalHierarchyService(db)
    result = await service.get_articles(
        chapter_id=chapter_id,
        skip=skip,
        limit=limit
    )
    return result


@router.put("/articles/{article_id}")
async def update_article(
    article_id: int = Path(..., gt=0, description="Article ID"),
    article_data: LawArticleUpdate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an article
    
    **All fields are optional:**
    - article_number: Update article number
    - title: Update article title
    - content: Update article content
    - keywords: Update keywords list
    - embedding: Update vector embedding
    - branch_id: Move to different branch
    - chapter_id: Move to different chapter
    - order_index: Update display order
    """
    service = LegalHierarchyService(db)
    result = await service.update_article(article_id, article_data)
    return result


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int = Path(..., gt=0, description="Article ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an article
    
    **⚠️ Warning:** This will permanently delete the article
    """
    service = LegalHierarchyService(db)
    result = await service.delete_article(article_id)
    return result

"""
Repository for persisting RAG query/answer logs.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models.query_log import QueryLog


class QueryLogRepository:
    """Data access layer for `QueryLog`."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_log(
        self,
        *,
        user_id: Optional[int],
        query: str,
        retrieved_articles: Optional[List[Dict[str, Any]]],
        generated_answer: Optional[str],
    ) -> QueryLog:
        log = QueryLog(
            user_id=user_id,
            query=query,
            retrieved_articles=retrieved_articles,
            generated_answer=generated_answer,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def list_recent(self, *, limit: int = 50) -> List[QueryLog]:
        result = await self.db.execute(
            select(QueryLog).order_by(desc(QueryLog.timestamp)).limit(limit)
        )
        return result.scalars().all()



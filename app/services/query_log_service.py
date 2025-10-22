"""
Service for logging RAG queries and answers.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.query_log_repository import QueryLogRepository


class QueryLogService:
    """Domain service to record query/answer activity for analytics and audit."""

    def __init__(self, db: AsyncSession) -> None:
        self.repository = QueryLogRepository(db)

    async def log_query_answer(
        self,
        *,
        user_id: Optional[int],
        query: str,
        retrieved_articles: Optional[List[Dict[str, Any]]],
        generated_answer: Optional[str],
    ) -> None:
        await self.repository.create_log(
            user_id=user_id,
            query=query,
            retrieved_articles=retrieved_articles,
            generated_answer=generated_answer,
        )



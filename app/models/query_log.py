"""
QueryLog model for storing user queries, retrieved articles, and generated answers.
"""

from typing import Optional

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from ..db.database import Base


class QueryLog(Base):
    """Persisted log entry for RAG query/answer cycles."""

    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    retrieved_articles = Column(JSON, nullable=True)
    generated_answer = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



# simplified_models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class LawDocument(Base):
    __tablename__ = "law_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    type = Column(String(100), default='law')
    jurisdiction = Column(String(200), index=True)
    original_filename = Column(String(500))
    file_size = Column(Integer)
    file_hash = Column(String(64), unique=True, index=True)
    status = Column(String(50), default='processing')
    total_chunks = Column(Integer, default=0)
    processed_chunks = Column(Integer, default=0)
    error_message = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    chunks = relationship("LawChunk", back_populates="document", cascade="all, delete-orphan")

class LawChunk(Base):
    __tablename__ = "law_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("law_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    word_count = Column(Integer)
    tokens_count = Column(Integer)
    embedding_vector = Column(JSON)
    chunk_index = Column(Integer, default=0)
    metadata = Column(JSON)
    embedding_model = Column(String(100), default='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    is_processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("LawDocument", back_populates="chunks")

# الفهارس
Index('idx_law_documents_status', LawDocument.status)
Index('idx_law_chunks_document_processed', LawChunk.document_id, LawChunk.is_processed)
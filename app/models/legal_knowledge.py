"""
Legal Knowledge Management Models - Clean and Hierarchical
Updated for hierarchical chunks and optimized relationships
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Float, Boolean,
    ForeignKey, CheckConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


# ---------------------------------------
# Law Sources
# ---------------------------------------
class LawSource(Base):
    """المصادر القانونية مثل القوانين واللوائح والأنظمة."""
    
    __tablename__ = "law_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, index=True)
    type = Column(String(50), CheckConstraint("type IN ('law', 'regulation', 'code', 'directive', 'decree')"))
    jurisdiction = Column(String(100), index=True)
    issuing_authority = Column(String(200))
    issue_date = Column(Date)
    last_update = Column(Date)
    description = Column(Text)
    source_url = Column(Text)
    knowledge_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    knowledge_document = relationship("KnowledgeDocument", foreign_keys=[knowledge_document_id])
    articles = relationship("LawArticle", back_populates="law_source", cascade="all, delete-orphan")
    chunks = relationship("KnowledgeChunk", back_populates="law_source")
    
    def __repr__(self):
        return f"<LawSource(id={self.id}, name='{self.name}', type='{self.type}')>"


# ---------------------------------------
# Law Articles
# ---------------------------------------
class LawArticle(Base):
    """المواد والفقرات القانونية مع الربط المباشر للمصدر القانوني."""
    
    __tablename__ = "law_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    law_source_id = Column(Integer, ForeignKey("law_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    article_number = Column(String(50), index=True)
    title = Column(Text)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # Store keywords as JSON array
    order_index = Column(Integer, default=0)  # ترتيب المواد داخل المصدر القانوني
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    law_source = relationship("LawSource", back_populates="articles")
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
    chunks = relationship("KnowledgeChunk", back_populates="article")
    
    def __repr__(self):
        return f"<LawArticle(id={self.id}, article_number='{self.article_number}', law_source_id={self.law_source_id})>"


# ---------------------------------------
# Legal Cases
# ---------------------------------------
class LegalCase(Base):
    """القضايا القانونية بما في ذلك السوابق والأحكام."""
    
    __tablename__ = "legal_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    jurisdiction = Column(String(100), index=True)
    court_name = Column(String(200))
    decision_date = Column(Date, index=True)
    case_type = Column(String(50), CheckConstraint("case_type IN ('مدني', 'جنائي', 'تجاري', 'عمل', 'إداري')"))
    court_level = Column(String(50), CheckConstraint("court_level IN ('ابتدائي', 'استئناف', 'تمييز', 'عالي')"))
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("KnowledgeDocument", foreign_keys=[document_id])
    sections = relationship("CaseSection", back_populates="case", cascade="all, delete-orphan")
    chunks = relationship("KnowledgeChunk", back_populates="legal_case")
    
    def __repr__(self):
        return f"<LegalCase(id={self.id}, case_number='{self.case_number}', title='{self.title[:50]}...')>"


# ---------------------------------------
# Case Sections
# ---------------------------------------
class CaseSection(Base):
    """Structured sections of legal cases."""
    
    __tablename__ = "case_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    section_type = Column(String(50), CheckConstraint("section_type IN ('summary', 'facts', 'arguments', 'ruling', 'legal_basis')"))
    content = Column(Text, nullable=False)
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    case = relationship("LegalCase", back_populates="sections")
    
    def __repr__(self):
        return f"<CaseSection(id={self.id}, case_id={self.case_id}, section_type='{self.section_type}')>"


# ---------------------------------------
# Legal Terms
# ---------------------------------------
class LegalTerm(Base):
    """Legal terms and definitions."""
    
    __tablename__ = "legal_terms"
    
    id = Column(Integer, primary_key=True, index=True)
    term = Column(Text, nullable=False, index=True)
    definition = Column(Text)
    source = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="legal_term")
    
    def __repr__(self):
        return f"<LegalTerm(id={self.id}, term='{self.term}', source='{self.source}')>"


# ---------------------------------------
# Knowledge Documents
# ---------------------------------------
class KnowledgeDocument(Base):
    """Documents uploaded for knowledge ingestion."""
    
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    category = Column(String(50), CheckConstraint("category IN ('law', 'case', 'contract', 'article', 'policy', 'manual')"))
    file_path = Column(Text)
    file_extension = Column(String(20), nullable=True)  # Store file extension (.json, .pdf, .docx, etc.)
    file_hash = Column(String(64), unique=True, index=True, nullable=True)
    source_type = Column(String(50), CheckConstraint("source_type IN ('uploaded', 'web_scraped', 'api_import')"))
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed', 'pending_parsing')"), default="raw")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    document_metadata = Column(JSON)
    
    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', category='{self.category}')>"


# ---------------------------------------
# Knowledge Chunks
# ---------------------------------------
class KnowledgeChunk(Base):
    """Atomic knowledge units for hierarchical storage."""
    
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tokens_count = Column(Integer)
    
    # Hierarchy
    law_source_id = Column(Integer, ForeignKey("law_sources.id"), nullable=True)
    article_id = Column(Integer, ForeignKey("law_articles.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("legal_cases.id"), nullable=True)
    term_id = Column(Integer, ForeignKey("legal_terms.id"), nullable=True)
    order_index = Column(Integer, default=0)
    
    verified_by_admin = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    law_source = relationship("LawSource", back_populates="chunks")
    article = relationship("LawArticle", back_populates="chunks")
    legal_case = relationship("LegalCase", back_populates="chunks")
    legal_term = relationship("LegalTerm", back_populates="chunks")
    
    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

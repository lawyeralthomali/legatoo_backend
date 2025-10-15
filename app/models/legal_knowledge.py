"""
Legal Knowledge Management Models - Enhanced with Hierarchical Structure
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Float, Boolean,
    ForeignKey, CheckConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


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

class LawArticle(Base):
    """المواد والفقرات القانونية مع الربط المباشر للمصدر القانوني."""
    
    __tablename__ = "law_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    law_source_id = Column(Integer, ForeignKey("law_sources.id", ondelete="CASCADE"), nullable=False, index=True) 
    article_number = Column(String(50), index=True)  # مثال: "75" أو "75/1"
    title = Column(Text)
    content = Column(Text, nullable=False)
    keywords = Column(JSON)
    embedding = Column(Text)
    order_index = Column(Integer, default=0)  # لترتيب المواد داخل المصدر القانوني
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - مع تحديد العلاقات بشكل صحيح
    law_source = relationship("LawSource", back_populates="articles")
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
    
    def __repr__(self):
        return f"<LawArticle(id={self.id}, article_number='{self.article_number}', law_source_id={self.law_source_id})>"


# باقي النماذج تبقى كما هي مع بعض التحسينات البسيطة
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


class CaseSection(Base):
    """Structured sections of legal cases."""
    
    __tablename__ = "case_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    section_type = Column(String(50), CheckConstraint("section_type IN ('summary', 'facts', 'arguments', 'ruling', 'legal_basis')"))
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # Store as text for SQLite, will be JSON-encoded vector
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    case = relationship("LegalCase", back_populates="sections")
    
    def __repr__(self):
        return f"<CaseSection(id={self.id}, case_id={self.case_id}, section_type='{self.section_type}')>"


class LegalTerm(Base):
    """Legal terms and definitions."""
    
    __tablename__ = "legal_terms"
    
    id = Column(Integer, primary_key=True, index=True)
    term = Column(Text, nullable=False, index=True)
    definition = Column(Text)
    source = Column(String(200))
    related_terms = Column(JSON)  # Store as JSON array for SQLite compatibility
    embedding = Column(Text)  # Store as text for SQLite, will be JSON-encoded vector
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="legal_term")
    
    def __repr__(self):
        return f"<LegalTerm(id={self.id}, term='{self.term}', source='{self.source}')>"


class KnowledgeDocument(Base):
    """Documents uploaded for knowledge ingestion."""
    
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    category = Column(String(50), CheckConstraint("category IN ('law', 'case', 'contract', 'article', 'policy', 'manual')"))
    file_path = Column(Text)
    file_hash = Column(String(64), unique=True, index=True, nullable=True)  # SHA-256 hash for duplicate detection
    source_type = Column(String(50), CheckConstraint("source_type IN ('uploaded', 'web_scraped', 'api_import')"))
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # FK to users table
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    document_metadata = Column(JSON)  # Flexible storage for structured information
    
    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', category='{self.category}')>"


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tokens_count = Column(Integer)
    embedding = Column(Text)  # Legacy field for backward compatibility
    embedding_vector = Column(JSON)  # New field for sentence-transformers embeddings
    verified_by_admin = Column(Boolean, default=False, index=True)
    
    # ✅ تحديث أسماء الحقول لتعكس الهيكل الجديد
    law_source_id = Column(Integer, ForeignKey("law_sources.id"), nullable=True)
    article_id = Column(Integer, ForeignKey("law_articles.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("legal_cases.id"), nullable=True) 
    term_id = Column(Integer, ForeignKey("legal_terms.id"), nullable=True)
    
    # ✅ تحديث العلاقات
    document = relationship("KnowledgeDocument", back_populates="chunks")
    law_source = relationship("LawSource", back_populates="chunks")
    article = relationship("LawArticle")
    legal_case = relationship("LegalCase", back_populates="chunks")
    legal_term = relationship("LegalTerm", back_populates="chunks")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class AnalysisResult(Base):
    """AI analysis outputs and summaries."""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), CheckConstraint("analysis_type IN ('summary', 'classification', 'entity_extraction', 'law_linking', 'case_linking')"))
    model_version = Column(String(100))
    output = Column(JSON, nullable=False)
    confidence = Column(Float)
    processed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="analysis_results")
    processor = relationship("User", foreign_keys=[processed_by])
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, document_id={self.document_id}, analysis_type='{self.analysis_type}')>"


class KnowledgeLink(Base):
    """Relationships between knowledge items."""
    
    __tablename__ = "knowledge_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    relation = Column(String(50), CheckConstraint("relation IN ('cites', 'interprets', 'contradicts', 'based_on', 'explains')"))
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeLink(id={self.id}, source='{self.source_type}:{self.source_id}', target='{self.target_type}:{self.target_id}')>"


class KnowledgeMetadata(Base):
    """Metadata tracking for knowledge ingestion and curation."""
    
    __tablename__ = "knowledge_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    object_type = Column(String(50), nullable=False, index=True)
    object_id = Column(Integer, nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeMetadata(id={self.id}, object='{self.object_type}:{self.object_id}', key='{self.key}')>"


# إنشاء فهارس إضافية للأداء
Index('idx_law_sources_type_jurisdiction', LawSource.type, LawSource.jurisdiction)
Index('idx_law_articles_source_order', LawArticle.law_source_id, LawArticle.order_index)
Index('idx_law_articles_keywords', LawArticle.keywords)
Index('idx_legal_cases_jurisdiction_date', LegalCase.jurisdiction, LegalCase.decision_date)
Index('idx_case_sections_type', CaseSection.section_type)
Index('idx_knowledge_documents_category_status', KnowledgeDocument.category, KnowledgeDocument.status)
Index('idx_knowledge_chunks_hierarchy', KnowledgeChunk.law_source_id, KnowledgeChunk.article_id, KnowledgeChunk.case_id)
Index('idx_knowledge_chunks_tokens', KnowledgeChunk.tokens_count)
Index('idx_analysis_results_type_confidence', AnalysisResult.analysis_type, AnalysisResult.confidence)
Index('idx_knowledge_links_source_target', KnowledgeLink.source_type, KnowledgeLink.source_id, KnowledgeLink.target_type, KnowledgeLink.target_id)
Index('idx_knowledge_metadata_object_key', KnowledgeMetadata.object_type, KnowledgeMetadata.object_id, KnowledgeMetadata.key)
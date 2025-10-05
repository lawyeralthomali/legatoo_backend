"""
Legal Knowledge Management schemas for FastAPI

This module defines Pydantic schemas for the legal knowledge management system,
including laws, cases, terms, documents, and analysis results.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from fastapi import UploadFile


# ===========================================
# ENUMS
# ===========================================

class LawSourceTypeEnum(str, Enum):
    """Law source type enumeration"""
    LAW = "law"
    REGULATION = "regulation"
    CODE = "code"
    DIRECTIVE = "directive"
    DECREE = "decree"


class CaseSectionTypeEnum(str, Enum):
    """Case section type enumeration"""
    SUMMARY = "summary"
    FACTS = "facts"
    ARGUMENTS = "arguments"
    RULING = "ruling"
    LEGAL_BASIS = "legal_basis"


class DocumentCategoryEnum(str, Enum):
    """Knowledge document category enumeration"""
    LAW = "law"
    CASE = "case"
    CONTRACT = "contract"
    ARTICLE = "article"
    POLICY = "policy"
    MANUAL = "manual"


class SourceTypeEnum(str, Enum):
    """Document source type enumeration"""
    UPLOADED = "uploaded"
    WEB_SCRAPED = "web_scraped"
    API_IMPORT = "api_import"


class DocumentStatusEnum(str, Enum):
    """Document processing status enumeration"""
    RAW = "raw"
    PROCESSED = "processed"
    INDEXED = "indexed"


class AnalysisTypeEnum(str, Enum):
    """Analysis type enumeration"""
    SUMMARY = "summary"
    CLASSIFICATION = "classification"
    ENTITY_EXTRACTION = "entity_extraction"
    LAW_LINKING = "law_linking"
    CASE_LINKING = "case_linking"


class KnowledgeRelationEnum(str, Enum):
    """Knowledge link relation enumeration"""
    CITES = "cites"
    INTERPRETS = "interprets"
    CONTRADICTS = "contradicts"
    BASED_ON = "based_on"
    EXPLAINS = "explains"


# ===========================================
# LAW SOURCES SCHEMAS
# ===========================================

class LawSourceBase(BaseModel):
    """Base law source schema"""
    name: str = Field(..., min_length=1, max_length=500)
    type: LawSourceTypeEnum
    jurisdiction: Optional[str] = Field(None, max_length=100)
    issuing_authority: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    last_update: Optional[date] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    knowledge_document_id: Optional[int] = None
    status: Optional[str] = Field(default='raw', pattern='^(raw|processed|indexed)$')


class LawSourceCreate(LawSourceBase):
    """Schema for creating a law source"""
    pass


class LawSourceUpdate(BaseModel):
    """Schema for updating a law source"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    type: Optional[LawSourceTypeEnum] = None
    jurisdiction: Optional[str] = Field(None, max_length=100)
    issuing_authority: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    last_update: Optional[date] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    knowledge_document_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern='^(raw|processed|indexed)$')


class LawSourceResponse(LawSourceBase):
    """Schema for law source response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    articles_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ===========================================
# LAW ARTICLES SCHEMAS
# ===========================================

# ===========================================
# LAW BRANCHES SCHEMAS
# ===========================================

class LawBranchBase(BaseModel):
    """Base law branch schema"""
    branch_number: Optional[str] = Field(None, max_length=20)
    branch_name: str = Field(..., min_length=1)
    description: Optional[str] = None
    order_index: Optional[int] = Field(default=0, ge=0)


class LawBranchCreate(LawBranchBase):
    """Schema for creating a law branch"""
    law_source_id: int = Field(..., gt=0)


class LawBranchUpdate(BaseModel):
    """Schema for updating a law branch"""
    branch_number: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)


class LawBranchResponse(LawBranchBase):
    """Schema for law branch response"""
    id: int
    law_source_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    chapters_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ===========================================
# LAW CHAPTERS SCHEMAS
# ===========================================

class LawChapterBase(BaseModel):
    """Base law chapter schema"""
    chapter_number: Optional[str] = Field(None, max_length=20)
    chapter_name: str = Field(..., min_length=1)
    description: Optional[str] = None
    order_index: Optional[int] = Field(default=0, ge=0)


class LawChapterCreate(LawChapterBase):
    """Schema for creating a law chapter"""
    branch_id: int = Field(..., gt=0)


class LawChapterUpdate(BaseModel):
    """Schema for updating a law chapter"""
    chapter_number: Optional[str] = Field(None, max_length=20)
    chapter_name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)


class LawChapterResponse(LawChapterBase):
    """Schema for law chapter response"""
    id: int
    branch_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    articles_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class LawArticleBase(BaseModel):
    """Base law article schema"""
    article_number: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = None
    content: str = Field(..., min_length=1)
    keywords: Optional[List[str]] = Field(default_factory=list)
    embedding: Optional[List[float]] = Field(default_factory=list)
    order_index: Optional[int] = Field(default=0, ge=0)


class LawArticleCreate(LawArticleBase):
    """Schema for creating a law article"""
    law_source_id: int = Field(..., gt=0)
    branch_id: Optional[int] = Field(None, gt=0)
    chapter_id: Optional[int] = Field(None, gt=0)


class LawArticleUpdate(BaseModel):
    """Schema for updating a law article"""
    article_number: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    keywords: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    branch_id: Optional[int] = Field(None, gt=0)
    chapter_id: Optional[int] = Field(None, gt=0)
    order_index: Optional[int] = Field(None, ge=0)


class LawArticleResponse(LawArticleBase):
    """Schema for law article response"""
    id: int
    law_source_id: int
    branch_id: Optional[int] = None
    chapter_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    law_source: Optional[LawSourceResponse] = None
    branch: Optional[LawBranchResponse] = None
    chapter: Optional[LawChapterResponse] = None
    
    class Config:
        from_attributes = True


# ===========================================
# LEGAL CASES SCHEMAS
# ===========================================

class LegalCaseBase(BaseModel):
    """Base legal case schema"""
    case_number: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    jurisdiction: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=200)
    decision_date: Optional[date] = None
    involved_parties: Optional[str] = None
    pdf_path: Optional[str] = None
    source_reference: Optional[str] = None
    case_type: Optional[str] = Field(None, max_length=50, description="نوع القضية: مدني، جنائي، تجاري، عمل، إداري")
    court_level: Optional[str] = Field(None, max_length=50, description="درجة المحكمة: ابتدائي، استئناف، تمييز، عالي")
    case_outcome: Optional[str] = Field(None, max_length=100, description="نتيجة القضية")
    judge_names: Optional[List[str]] = Field(None, description="أسماء القضاة")
    claim_amount: Optional[float] = Field(None, ge=0, description="مبلغ المطالبة")


class LegalCaseCreate(LegalCaseBase):
    """Schema for creating a legal case"""
    pass


class LegalCaseUpdate(BaseModel):
    """Schema for updating a legal case"""
    case_number: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    jurisdiction: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=200)
    decision_date: Optional[date] = None
    involved_parties: Optional[str] = None
    pdf_path: Optional[str] = None
    source_reference: Optional[str] = None
    case_type: Optional[str] = Field(None, max_length=50, description="نوع القضية: مدني، جنائي، تجاري، عمل، إداري")
    court_level: Optional[str] = Field(None, max_length=50, description="درجة المحكمة: ابتدائي، استئناف، تمييز، عالي")
    case_outcome: Optional[str] = Field(None, max_length=100, description="نتيجة القضية")
    judge_names: Optional[List[str]] = Field(None, description="أسماء القضاة")
    claim_amount: Optional[float] = Field(None, ge=0, description="مبلغ المطالبة")


class LegalCaseResponse(LegalCaseBase):
    """Schema for legal case response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sections_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ===========================================
# CASE SECTIONS SCHEMAS
# ===========================================

class CaseSectionBase(BaseModel):
    """Base case section schema"""
    section_type: CaseSectionTypeEnum
    content: str = Field(..., min_length=1)
    embedding: Optional[List[float]] = Field(default_factory=list)


class CaseSectionCreate(CaseSectionBase):
    """Schema for creating a case section"""
    case_id: int = Field(..., gt=0)


class CaseSectionUpdate(BaseModel):
    """Schema for updating a case section"""
    section_type: Optional[CaseSectionTypeEnum] = None
    content: Optional[str] = Field(None, min_length=1)
    embedding: Optional[List[float]] = None


class CaseSectionResponse(CaseSectionBase):
    """Schema for case section response"""
    id: int
    case_id: int
    created_at: datetime
    case: Optional[LegalCaseResponse] = None
    
    class Config:
        from_attributes = True


# ===========================================
# LEGAL TERMS SCHEMAS
# ===========================================

class LegalTermBase(BaseModel):
    """Base legal term schema"""
    term: str = Field(..., min_length=1)
    definition: Optional[str] = None
    source: Optional[str] = Field(None, max_length=200)
    related_terms: Optional[List[str]] = Field(default_factory=list)
    embedding: Optional[List[float]] = Field(default_factory=list)


class LegalTermCreate(LegalTermBase):
    """Schema for creating a legal term"""
    pass


class LegalTermUpdate(BaseModel):
    """Schema for updating a legal term"""
    term: Optional[str] = Field(None, min_length=1)
    definition: Optional[str] = None
    source: Optional[str] = Field(None, max_length=200)
    related_terms: Optional[List[str]] = None
    embedding: Optional[List[float]] = None


class LegalTermResponse(LegalTermBase):
    """Schema for legal term response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# KNOWLEDGE DOCUMENTS SCHEMAS
# ===========================================

class KnowledgeDocumentBase(BaseModel):
    """Base knowledge document schema"""
    title: str = Field(..., min_length=1)
    category: DocumentCategoryEnum
    file_path: Optional[str] = None
    source_type: SourceTypeEnum = Field(default=SourceTypeEnum.UPLOADED)
    status: DocumentStatusEnum = Field(default=DocumentStatusEnum.RAW)
    uploaded_by: Optional[int] = None
    document_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """Schema for creating a knowledge document"""
    pass


class KnowledgeDocumentUpdate(BaseModel):
    """Schema for updating a knowledge document"""
    title: Optional[str] = Field(None, min_length=1)
    category: Optional[DocumentCategoryEnum] = None
    file_path: Optional[str] = None
    source_type: Optional[SourceTypeEnum] = None
    status: Optional[DocumentStatusEnum] = None
    document_metadata: Optional[Dict[str, Any]] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    """Schema for knowledge document response"""
    id: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    chunks_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ===========================================
# KNOWLEDGE CHUNKS SCHEMAS
# ===========================================

class KnowledgeChunkBase(BaseModel):
    """Base knowledge chunk schema"""
    chunk_index: int = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    tokens_count: Optional[int] = None
    embedding: Optional[List[float]] = Field(default_factory=list)
    law_source_ref: Optional[int] = None
    case_ref: Optional[int] = None
    term_ref: Optional[int] = None


class KnowledgeChunkCreate(KnowledgeChunkBase):
    """Schema for creating a knowledge chunk"""
    document_id: int = Field(..., gt=0)


class KnowledgeChunkUpdate(BaseModel):
    """Schema for updating a knowledge chunk"""
    chunk_index: Optional[int] = Field(None, ge=0)
    content: Optional[str] = Field(None, min_length=1)
    tokens_count: Optional[int] = None
    embedding: Optional[List[float]] = None
    law_source_ref: Optional[int] = None
    case_ref: Optional[int] = None
    term_ref: Optional[int] = None


class KnowledgeChunkResponse(KnowledgeChunkBase):
    """Schema for knowledge chunk response"""
    id: int
    document_id: int
    created_at: datetime
    document: Optional[KnowledgeDocumentResponse] = None
    
    class Config:
        from_attributes = True


# ===========================================
# ARABIC DOCUMENT PROCESSING SCHEMAS
# ===========================================

class ArabicDocumentProcessRequest(BaseModel):
    """Schema for Arabic document processing request with file upload"""
    law_source_details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional existing law source details"
    )
    uploaded_by: Optional[int] = Field(None, description="User ID who uploaded the document")


class MultipleDocumentsProcessRequest(BaseModel):
    """Schema for processing multiple Arabic documents"""
    file_paths: List[str] = Field(..., min_items=1, max_items=10, description="List of file paths")
    law_source_details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional existing law source details"
    )
    uploaded_by: Optional[int] = Field(None, description="User ID who uploaded the documents")


class TextExtractionRequest(BaseModel):
    """Schema for text extraction request"""
    text: str = Field(..., min_length=100, description="Arabic legal text")
    existing_details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional existing law source details to merge"
    )


class ArticleExtractionRequest(BaseModel):
    """Schema for article extraction request"""
    text: str = Field(..., min_length=100, description="Arabic legal text")
    law_source_id: Optional[int] = Field(None, description="Law source ID to associate articles with")


# ===========================================
# ANALYSIS RESULTS SCHEMAS
# ===========================================

class AnalysisResultBase(BaseModel):
    """Base analysis result schema"""
    analysis_type: AnalysisTypeEnum
    model_version: Optional[str] = Field(None, max_length=100)
    output: Dict[str, Any]
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating an analysis result"""
    document_id: int = Field(..., gt=0)


class AnalysisResultUpdate(BaseModel):
    """Schema for updating an analysis result"""
    analysis_type: Optional[AnalysisTypeEnum] = None
    model_version: Optional[str] = Field(None, max_length=100)
    output: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AnalysisResultResponse(AnalysisResultBase):
    """Schema for analysis result response"""
    id: int
    document_id: int
    created_at: datetime
    document: Optional[KnowledgeDocumentResponse] = None
    
    class Config:
        from_attributes = True


# ===========================================
# KNOWLEDGE LINKS SCHEMAS
# ===========================================

class KnowledgeLinkBase(BaseModel):
    """Base knowledge link schema"""
    source_type: str = Field(..., max_length=50)
    source_id: int = Field(..., gt=0)
    target_type: str = Field(..., max_length=50)
    target_id: int = Field(..., gt=0)
    relation: KnowledgeRelationEnum
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class KnowledgeLinkCreate(KnowledgeLinkBase):
    """Schema for creating a knowledge link"""
    pass


class KnowledgeLinkUpdate(BaseModel):
    """Schema for updating a knowledge link"""
    relation: Optional[KnowledgeRelationEnum] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)


class KnowledgeLinkResponse(KnowledgeLinkBase):
    """Schema for knowledge link response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# KNOWLEDGE METADATA SCHEMAS
# ===========================================

class KnowledgeMetadataBase(BaseModel):
    """Base knowledge metadata schema"""
    object_type: str = Field(..., max_length=50)
    object_id: int = Field(..., gt=0)
    key: str = Field(..., max_length=100)
    value: Optional[str] = None


class KnowledgeMetadataCreate(KnowledgeMetadataBase):
    """Schema for creating knowledge metadata"""
    pass


class KnowledgeMetadataUpdate(BaseModel):
    """Schema for updating knowledge metadata"""
    key: Optional[str] = Field(None, max_length=100)
    value: Optional[str] = None


class KnowledgeMetadataResponse(KnowledgeMetadataBase):
    """Schema for knowledge metadata response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# SEARCH AND FILTER SCHEMAS
# ===========================================

class LegalKnowledgeSearchRequest(BaseModel):
    """Schema for legal knowledge search request"""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: Optional[str] = Field(None, description="Type of content to search: 'all', 'laws', 'cases', 'terms'")
    jurisdiction: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class LegalKnowledgeSearchResponse(BaseModel):
    """Schema for legal knowledge search response"""
    results: List[Dict[str, Any]]
    total: int
    query: str
    search_type: str


class KnowledgeStatsResponse(BaseModel):
    """Schema for knowledge statistics response"""
    total_law_sources: int
    total_articles: int
    total_cases: int
    total_terms: int
    total_documents: int
    total_chunks: int
    sources_by_type: Dict[str, int]
    cases_by_jurisdiction: Dict[str, int]
    documents_by_category: Dict[str, int]


# ===========================================
# BULK OPERATIONS SCHEMAS
# ===========================================

class BulkLawSourceCreate(BaseModel):
    """Schema for bulk law source creation"""
    sources: List[LawSourceCreate] = Field(..., min_items=1, max_items=100)


class BulkLawArticleCreate(BaseModel):
    """Schema for bulk law article creation"""
    articles: List[LawArticleCreate] = Field(..., min_items=1, max_items=100)


class BulkLegalCaseCreate(BaseModel):
    """Schema for bulk legal case creation"""
    cases: List[LegalCaseCreate] = Field(..., min_items=1, max_items=100)


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response"""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_ids: List[int] = Field(default_factory=list)


# ===========================================
# PAGINATION SCHEMAS
# ===========================================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Schema for paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# ===========================================
# HIERARCHICAL DOCUMENT STRUCTURE SCHEMAS
# ===========================================

class DocumentStructureElement(BaseModel):
    """Base schema for document structure elements"""
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this element")
    warnings: Optional[List[str]] = Field(default_factory=list, description="Any warnings about this element")
    errors: Optional[List[str]] = Field(default_factory=list, description="Any errors detected")


class ArticleStructure(DocumentStructureElement):
    """Schema for article structure"""
    number: str = Field(..., description="Article number (e.g., '1', '15/2')")
    title: Optional[str] = Field(None, description="Article title")
    content: str = Field(..., min_length=1, description="Article content")
    sub_articles: Optional[List['ArticleStructure']] = Field(default_factory=list, description="Sub-articles")
    order_index: int = Field(default=0, ge=0, description="Order within chapter")


class SectionStructure(DocumentStructureElement):
    """Schema for section structure"""
    number: str = Field(..., description="Section number (e.g., '1', 'أولاً')")
    title: str = Field(..., min_length=1, description="Section title")
    description: Optional[str] = Field(None, description="Section description")
    articles: List[ArticleStructure] = Field(default_factory=list, description="Articles in this section")
    order_index: int = Field(default=0, ge=0, description="Order within branch")


class ChapterStructure(DocumentStructureElement):
    """Schema for chapter structure"""
    number: str = Field(..., description="Chapter number (e.g., '1', 'أول')")
    title: str = Field(..., min_length=1, description="Chapter title")
    description: Optional[str] = Field(None, description="Chapter description")
    sections: List[SectionStructure] = Field(default_factory=list, description="Sections in this chapter")
    articles: List[ArticleStructure] = Field(default_factory=list, description="Direct articles (not in sections)")
    order_index: int = Field(default=0, ge=0, description="Order within document")


class DocumentStructure(BaseModel):
    """Schema for complete document structure"""
    chapters: List[ChapterStructure] = Field(default_factory=list, description="Document chapters")
    orphaned_articles: List[ArticleStructure] = Field(default_factory=list, description="Articles not in any chapter/section")
    total_chapters: int = Field(default=0, ge=0)
    total_sections: int = Field(default=0, ge=0)
    total_articles: int = Field(default=0, ge=0)
    structure_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall structure confidence")


class ProcessingReport(BaseModel):
    """Schema for document processing report"""
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    processing_time: Optional[float] = Field(None, ge=0, description="Processing time in seconds")
    text_length: Optional[int] = Field(None, ge=0, description="Total text length processed")
    pages_processed: Optional[int] = Field(None, ge=0, description="Number of pages processed")


class HierarchicalDocumentResponse(BaseModel):
    """Schema for hierarchical document processing response"""
    document: LawSourceResponse = Field(..., description="Created law source")
    structure: DocumentStructure = Field(..., description="Extracted document structure")
    processing_report: ProcessingReport = Field(..., description="Processing report and metrics")


class StructureValidationRequest(BaseModel):
    """Schema for structure validation request"""
    law_source_id: int = Field(..., gt=0, description="Law source ID to validate")
    validate_numbering: bool = Field(default=True, description="Validate numbering continuity")
    validate_hierarchy: bool = Field(default=True, description="Validate parent-child relationships")
    detect_gaps: bool = Field(default=True, description="Detect missing elements")


class StructureValidationResponse(BaseModel):
    """Schema for structure validation response"""
    is_valid: bool = Field(..., description="Whether structure is valid")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall validation confidence")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Detected issues")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Structure statistics")


class StructureCorrectionRequest(BaseModel):
    """Schema for structure correction request"""
    law_source_id: int = Field(..., gt=0, description="Law source ID")
    corrections: List[Dict[str, Any]] = Field(..., min_items=1, description="List of corrections to apply")


class StructureCorrectionResponse(BaseModel):
    """Schema for structure correction response"""
    success: bool = Field(..., description="Whether corrections were applied successfully")
    corrections_applied: int = Field(..., ge=0, description="Number of corrections applied")
    remaining_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Remaining issues after correction")
    updated_structure: Optional[DocumentStructure] = Field(None, description="Updated structure after corrections")


# Update forward references
ArticleStructure.model_rebuild()
SectionStructure.model_rebuild()
ChapterStructure.model_rebuild()

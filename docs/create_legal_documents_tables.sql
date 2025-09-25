-- Create legal documents tables
-- Converted from Django models to PostgreSQL

-- Create legal_documents table
CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    uploaded_by_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    document_type VARCHAR(50) NOT NULL DEFAULT 'other',
    language VARCHAR(10) NOT NULL DEFAULT 'ar',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT
);

-- Create legal_document_chunks table
CREATE TABLE IF NOT EXISTS legal_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    article_number VARCHAR(50),
    section_title VARCHAR(255),
    keywords JSONB DEFAULT '[]'::jsonb,
    embedding JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_legal_documents_uploaded_by ON legal_documents(uploaded_by_id);
CREATE INDEX IF NOT EXISTS idx_legal_documents_document_type ON legal_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_legal_documents_language ON legal_documents(language);
CREATE INDEX IF NOT EXISTS idx_legal_documents_created_at ON legal_documents(created_at);
CREATE INDEX IF NOT EXISTS idx_legal_documents_processing_status ON legal_documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_legal_document_chunks_document_id ON legal_document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_legal_document_chunks_chunk_index ON legal_document_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_legal_document_chunks_article_number ON legal_document_chunks(article_number);

-- Add constraints
ALTER TABLE legal_documents ADD CONSTRAINT check_title_length CHECK (length(title) >= 1 AND length(title) <= 255);
ALTER TABLE legal_documents ADD CONSTRAINT check_file_path_length CHECK (length(file_path) >= 1 AND length(file_path) <= 500);
ALTER TABLE legal_documents ADD CONSTRAINT check_document_type CHECK (document_type IN ('employment_contract', 'partnership_contract', 'service_contract', 'lease_contract', 'sales_contract', 'labor_law', 'commercial_law', 'civil_law', 'other'));
ALTER TABLE legal_documents ADD CONSTRAINT check_language CHECK (language IN ('ar', 'en', 'fr'));
ALTER TABLE legal_documents ADD CONSTRAINT check_processing_status CHECK (processing_status IN ('pending', 'processing', 'done', 'error'));

ALTER TABLE legal_document_chunks ADD CONSTRAINT check_chunk_index CHECK (chunk_index >= 1);
ALTER TABLE legal_document_chunks ADD CONSTRAINT check_content_length CHECK (length(content) >= 1);
ALTER TABLE legal_document_chunks ADD CONSTRAINT check_article_number_length CHECK (article_number IS NULL OR length(article_number) <= 50);
ALTER TABLE legal_document_chunks ADD CONSTRAINT check_section_title_length CHECK (section_title IS NULL OR length(section_title) <= 255);

-- Add comments
COMMENT ON TABLE legal_documents IS 'Stores legal documents uploaded by users';
COMMENT ON TABLE legal_document_chunks IS 'Stores chunks of legal documents with embeddings for semantic search';

COMMENT ON COLUMN legal_documents.id IS 'Unique identifier for the document';
COMMENT ON COLUMN legal_documents.title IS 'Title of the legal document';
COMMENT ON COLUMN legal_documents.file_path IS 'Path to the uploaded file';
COMMENT ON COLUMN legal_documents.uploaded_by_id IS 'ID of the user who uploaded the document';
COMMENT ON COLUMN legal_documents.document_type IS 'Type of legal document';
COMMENT ON COLUMN legal_documents.language IS 'Language of the document';
COMMENT ON COLUMN legal_documents.is_processed IS 'Whether the document has been processed for chunks';
COMMENT ON COLUMN legal_documents.processing_status IS 'Current processing status';
COMMENT ON COLUMN legal_documents.notes IS 'Optional notes about the document';

COMMENT ON COLUMN legal_document_chunks.id IS 'Unique identifier for the chunk';
COMMENT ON COLUMN legal_document_chunks.document_id IS 'Reference to the parent document';
COMMENT ON COLUMN legal_document_chunks.chunk_index IS 'Index of the chunk within the document';
COMMENT ON COLUMN legal_document_chunks.content IS 'Text content of the chunk';
COMMENT ON COLUMN legal_document_chunks.article_number IS 'Article number if detected in the chunk';
COMMENT ON COLUMN legal_document_chunks.section_title IS 'Section title if detected';
COMMENT ON COLUMN legal_document_chunks.keywords IS 'Keywords extracted from the chunk';
COMMENT ON COLUMN legal_document_chunks.embedding IS 'Vector embedding for semantic search';

"""
Legal Document Parser Service with Dual Database Support

This module provides comprehensive parsing functionality for legal documents with
synchronized support for both SQL database and Chroma Vectorstore.

Features:
- Dual database synchronization (SQL + Chroma)
- Singleton pattern for embeddings and vectorstore
- Automatic rollback on failures
- Flexible deletion and updates
- Comprehensive error handling
"""

import json
import logging
import hashlib
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from ....models.legal_knowledge import (
    KnowledgeDocument, LawSource, LawArticle, KnowledgeChunk,
    LegalCase, CaseSection, LegalTerm
)
from ....schemas.document_upload import (
    LawSourceSummary, LawArticleSummary, KnowledgeChunkSummary,
    BulkOperationResult, DocumentProcessingStats
)

logger = logging.getLogger(__name__)

# ---------------------------------
# Global Configuration and Constants
# ---------------------------------
VECTORSTORE_PATH = "./chroma_store"
os.makedirs(VECTORSTORE_PATH, exist_ok=True)

# Performance optimization settings
EMBEDDING_MODEL = "Omartificial-Intelligence-Space/GATE-AraBert-v1"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
BATCH_SIZE = 50

# ---------------------------------
# Singleton Vectorstore Manager
# ---------------------------------
class VectorstoreManager:
    """
    Singleton manager for Chroma vectorstore and embeddings.
    Ensures single instance and proper synchronization with SQL database.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_vectorstore()
            self._initialized = True
    
    def _initialize_vectorstore(self):
        """Initialize Chroma vectorstore and embeddings."""
        logger.info("🚀 Initializing VectorstoreManager...")
        
        try:
            # استخدام embeddings بسيط للاختبار (أسرع وأكثر استقراراً)
            logger.warning("⚠️ Using simple embeddings for testing...")
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=768)  # استخدام البعد الصحيح
            
            # Initialize Chroma vectorstore
            self.vectorstore = Chroma(
                collection_name="legal_knowledge",
                embedding_function=self.embeddings,
                persist_directory=VECTORSTORE_PATH,
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP
            )
            
            logger.info("✅ VectorstoreManager initialized with simple embeddings!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize VectorstoreManager: {e}")
            raise
    
    def get_vectorstore(self) -> Chroma:
        """Get Chroma vectorstore instance."""
        return self.vectorstore
    
    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """Get embeddings instance."""
        return self.embeddings
    
    def get_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Get text splitter instance."""
        return self.text_splitter

# Global instance
vectorstore_manager = VectorstoreManager()

# ---------------------------------
# Dual Database Operations Manager
# ---------------------------------
class DualDatabaseManager:
    """
    Manages synchronized operations between SQL database and Chroma vectorstore.
    Ensures data consistency and provides rollback capabilities.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.vectorstore = vectorstore_manager.get_vectorstore()
        self.text_splitter = vectorstore_manager.get_text_splitter()
    
    async def add_chunk_to_both_databases(
        self,
        chunk: KnowledgeChunk,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add chunk to both SQL database and Chroma vectorstore.
        Returns True if successful, False otherwise.
        """
        try:
            # Add to SQL database
            self.db.add(chunk)
            await self.db.commit()
            await self.db.refresh(chunk)
            
            # Prepare metadata for Chroma (ensure compatibility)
            chroma_metadata = self._prepare_chroma_metadata(metadata, chunk)
            
            # Add to Chroma vectorstore
            self.vectorstore.add_texts(
                texts=[content],
                metadatas=[chroma_metadata],
                ids=[str(chunk.id)]  # Use SQL ID as Chroma ID for synchronization
            )
            
            # Persist Chroma changes
            self.vectorstore.persist()
            
            logger.info(f"✅ Chunk {chunk.id} added to both databases")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add chunk to both databases: {e}")
            await self.db.rollback()
            return False
    
    async def update_chunk_in_both_databases(
        self,
        chunk_id: int,
        new_content: str,
        new_metadata: Dict[str, Any]
    ) -> bool:
        """
        Update chunk in both SQL database and Chroma vectorstore.
        """
        try:
            # Update SQL database
            chunk = await self.db.get(KnowledgeChunk, chunk_id)
            if not chunk:
                logger.error(f"❌ Chunk {chunk_id} not found in SQL database")
                return False
            
            chunk.content = new_content
            chunk.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Update Chroma vectorstore
            chroma_metadata = self._prepare_chroma_metadata(new_metadata, chunk)
            
            # Delete old entry and add new one
            self.vectorstore.delete(ids=[str(chunk_id)])
            self.vectorstore.add_texts(
                texts=[new_content],
                metadatas=[chroma_metadata],
                ids=[str(chunk_id)]
            )
            self.vectorstore.persist()
            
            logger.info(f"✅ Chunk {chunk_id} updated in both databases")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update chunk {chunk_id}: {e}")
            await self.db.rollback()
            return False
    
    async def delete_chunk_from_both_databases(self, chunk_id: int) -> bool:
        """
        Delete chunk from both SQL database and Chroma vectorstore.
        """
        try:
            # Delete from SQL database
            chunk = await self.db.get(KnowledgeChunk, chunk_id)
            if chunk:
                await self.db.delete(chunk)
                await self.db.commit()
            
            # Delete from Chroma vectorstore
            self.vectorstore.delete(ids=[str(chunk_id)])
            self.vectorstore.persist()
            
            logger.info(f"✅ Chunk {chunk_id} deleted from both databases")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete chunk {chunk_id}: {e}")
            await self.db.rollback()
            return False
    
    async def delete_document_from_both_databases(self, document_id: int) -> bool:
        """
        Delete document and all its chunks from both databases.
        """
        try:
            # Get all chunks for this document
            chunks_result = await self.db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
            )
            chunks = chunks_result.scalars().all()
            
            # Delete chunks from Chroma first
            chunk_ids = [str(chunk.id) for chunk in chunks]
            if chunk_ids:
                self.vectorstore.delete(ids=chunk_ids)
                self.vectorstore.persist()
            
            # Delete document from SQL (cascade will handle chunks)
            document = await self.db.get(KnowledgeDocument, document_id)
            if document:
                await self.db.delete(document)
                await self.db.commit()
            
            logger.info(f"✅ Document {document_id} and {len(chunks)} chunks deleted from both databases")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document {document_id}: {e}")
            await self.db.rollback()
            return False
    
    def _prepare_chroma_metadata(self, metadata: Dict[str, Any], chunk: KnowledgeChunk) -> Dict[str, Any]:
        """
        Prepare metadata for Chroma vectorstore compatibility.
        Ensures all values are serializable and includes required fields.
        """
        chroma_metadata = {
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "tokens_count": chunk.tokens_count or 0,
            "verified_by_admin": chunk.verified_by_admin,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None
        }
        
        # Add optional references
        if chunk.law_source_id:
            chroma_metadata["law_source_id"] = chunk.law_source_id
        if chunk.article_id:
            chroma_metadata["article_id"] = chunk.article_id
        if chunk.case_id:
            chroma_metadata["case_id"] = chunk.case_id
        if chunk.term_id:
            chroma_metadata["term_id"] = chunk.term_id
        
        # Add custom metadata
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                chroma_metadata[key] = value
            elif isinstance(value, list):
                try:
                    chroma_metadata[key] = ", ".join(map(str, value))
                except Exception:
                    chroma_metadata[key] = str(value)
            else:
                chroma_metadata[key] = str(value)
        
        return chroma_metadata
    
    async def sync_database_states(self) -> Dict[str, int]:
        """
        Synchronize SQL and Chroma databases.
        Returns statistics about synchronization.
        """
        try:
            stats = {
                "sql_chunks": 0,
                "chroma_chunks": 0,
                "missing_in_chroma": 0,
                "missing_in_sql": 0,
                "synced": 0
            }
            
            # Get all chunks from SQL
            sql_result = await self.db.execute(select(KnowledgeChunk))
            sql_chunks = sql_result.scalars().all()
            stats["sql_chunks"] = len(sql_chunks)
            
            # Get all chunks from Chroma
            chroma_collection = self.vectorstore._collection
            chroma_chunks = chroma_collection.get()
            stats["chroma_chunks"] = len(chroma_chunks.get("ids", []))
            
            # Find missing chunks
            sql_ids = {str(chunk.id) for chunk in sql_chunks}
            chroma_ids = set(chroma_chunks.get("ids", []))
            
            missing_in_chroma = sql_ids - chroma_ids
            missing_in_sql = chroma_ids - sql_ids
            
            stats["missing_in_chroma"] = len(missing_in_chroma)
            stats["missing_in_sql"] = len(missing_in_sql)
            stats["synced"] = len(sql_ids & chroma_ids)            
            logger.info(f"📊 Database sync stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to sync database states: {e}")
            return {}


class LegalDocumentParser:
    """
    Enhanced parser for legal documents with dual database support.
    
    This class provides comprehensive parsing functionality with synchronized
    support for both SQL database and Chroma vectorstore.
    
    Supported file types:
    - JSON: Fully implemented with dual database support
    - PDF: Placeholder for future implementation
    - DOCX: Placeholder for future implementation
    - TXT: Placeholder for future implementation
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.dual_db_manager = DualDatabaseManager(db_session)
        self.processing_stats = DocumentProcessingStats(
            total_processing_time=0.0,
            file_parsing_time=0.0,
            database_operations_time=0.0,
            chunk_creation_time=0.0
        )
    
    async def parse_document(
        self, 
        file_path: str, 
        document: KnowledgeDocument,
        metadata: Dict[str, Any]
    ) -> Tuple[List[LawSourceSummary], List[LawArticleSummary], List[KnowledgeChunkSummary]]:
       
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.json':
            return await self._parse_json_document(file_path, document, metadata)
        elif file_extension == '.pdf':
            return await self._parse_pdf_document(file_path, document, metadata)
        elif file_extension in ['.docx', '.doc']:
            return await self._parse_docx_document(file_path, document, metadata)
        elif file_extension == '.txt':
            return await self._parse_txt_document(file_path, document, metadata)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    async def _parse_json_document(
        self, 
        file_path: str, 
        document: KnowledgeDocument,
        metadata: Dict[str, Any]
    ) -> Tuple[List[LawSourceSummary], List[LawArticleSummary], List[KnowledgeChunkSummary]]:
     
        logger.info(f"🔄 Starting JSON parsing for document: {document.title}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            logger.info(f"📋 JSON structure keys: {list(json_data.keys())}")
            logger.info(f"📋 JSON data type: {type(json_data)}")
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                # If the JSON is a list of law sources directly
                law_sources_data = json_data
            elif isinstance(json_data, dict):
                if 'law_sources' in json_data:
                    law_sources_value = json_data['law_sources']
                    # Handle both single object and array cases
                    if isinstance(law_sources_value, list):
                        law_sources_data = law_sources_value
                    else:
                        # Single law source object - wrap in array
                        law_sources_data = [law_sources_value]
                elif 'law_source' in json_data:
                    # Handle singular 'law_source' key
                    law_sources_data = [json_data['law_source']]
                else:
                    # If the JSON is a single law source object
                    law_sources_data = [json_data]
            else:
                raise ValueError(f"Unexpected JSON structure: {type(json_data)}")
            
            if not isinstance(law_sources_data, list):
                raise ValueError("Law sources data must be a list")
            
            law_sources_summary = []
            articles_summary = []
            chunks_summary = []
            
            # Process each law source
            for i, law_source_data in enumerate(law_sources_data):
                logger.info(f"📋 Processing law source {i+1}: {type(law_source_data)}")
                
                # Ensure law_source_data is a dictionary
                if not isinstance(law_source_data, dict):
                    logger.error(f"❌ Law source data is not a dictionary: {type(law_source_data)}")
                    continue
                
                # Validate required fields
                if 'name' not in law_source_data:
                    logger.error(f"❌ Law source {i+1} missing 'name' field")
                    continue
                
                # Create or update law source
                law_source = await self._process_law_source(law_source_data, document)
                law_sources_summary.append(LawSourceSummary(
                    id=law_source.id,
                    name=law_source.name,
                    type=law_source.type,
                    jurisdiction=law_source.jurisdiction,
                    issuing_authority=law_source.issuing_authority,
                    issue_date=law_source.issue_date.isoformat() if law_source.issue_date else None,
                    articles_count=len(law_source_data.get('articles', []))
                ))
                
                # Process articles for this law source
                if 'articles' in law_source_data:
                    articles_data = law_source_data['articles']
                    if isinstance(articles_data, list):
                        logger.info(f"🔄 معالجة {len(articles_data)} مادة...")
                        
                        for i, article_data in enumerate(articles_data):
                            try:
                                if isinstance(article_data, dict):
                                    logger.info(f"📄 معالجة المادة {i+1}/{len(articles_data)}: {article_data.get('article', 'غير محدد')}")
                                    
                                    article = await self._process_law_article(article_data, law_source, document)
                                    articles_summary.append(LawArticleSummary(
                                        id=article.id,
                                        article_number=article.article_number,
                                        title=article.title,
                                        order_index=article.order_index
                                    ))
                                    
                                    # Create knowledge chunks for this article
                                    try:
                                        article_chunks = await self._create_knowledge_chunks(
                                            article, law_source, document
                                        )
                                        chunks_summary.extend(article_chunks)
                                        logger.info(f"✅ تم إنشاء {len(article_chunks)} chunks للمادة {article.article_number}")
                                    except Exception as chunk_error:
                                        logger.error(f"❌ فشل في إنشاء chunks للمادة {article.article_number}: {chunk_error}")
                                        # استمرار مع المادة التالية بدلاً من التوقف
                                        continue
                                else:
                                    logger.warning(f"⚠️ بيانات المادة {i+1} ليست dictionary: {type(article_data)}")
                            except Exception as article_error:
                                logger.error(f"❌ فشل في معالجة المادة {i+1}: {article_error}")
                                # استمرار مع المادة التالية بدلاً من التوقف
                                continue
                    else:
                        logger.warning(f"⚠️ بيانات المواد ليست list: {type(articles_data)}")
            
            logger.info(f"✅ JSON parsing completed: {len(law_sources_summary)} sources, "
                       f"{len(articles_summary)} articles, {len(chunks_summary)} chunks")
            
            return law_sources_summary, articles_summary, chunks_summary
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"❌ JSON document processing failed: {e}")
            raise
    
    async def _process_law_source(
        self, 
        law_source_data: Dict[str, Any], 
        document: KnowledgeDocument
    ) -> LawSource:
        """Create or update a law source from JSON data."""
        
        # Check if law source already exists by name and type
        existing_source = await self.db.execute(
            select(LawSource).where(
                LawSource.name == law_source_data['name'],
                LawSource.type == law_source_data.get('type', 'law')
            )
        )
        existing_source = existing_source.scalar_one_or_none()
        
        if existing_source:
            # Update existing law source
            existing_source.jurisdiction = law_source_data.get('jurisdiction')
            existing_source.issuing_authority = law_source_data.get('issuing_authority')
            existing_source.last_update = self._parse_date(law_source_data.get('last_update'))
            existing_source.description = law_source_data.get('description')
            existing_source.source_url = law_source_data.get('source_url')
            existing_source.knowledge_document_id = document.id
            existing_source.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(existing_source)
            
            logger.info(f"📝 Updated existing law source: {existing_source.name}")
            return existing_source
        else:
            # Create new law source
            new_source = LawSource(
                name=law_source_data['name'],
                type=law_source_data.get('type', 'law'),
                jurisdiction=law_source_data.get('jurisdiction'),
                issuing_authority=law_source_data.get('issuing_authority'),
                issue_date=self._parse_date(law_source_data.get('issue_date')),
                last_update=self._parse_date(law_source_data.get('last_update')),
                description=law_source_data.get('description'),
                source_url=law_source_data.get('source_url'),
                knowledge_document_id=document.id,
                status='processed'
            )
            
            self.db.add(new_source)
            await self.db.commit()
            await self.db.refresh(new_source)
            
            logger.info(f"✨ Created new law source: {new_source.name}")
            return new_source
    
    async def _process_law_article(
        self, 
        article_data: Dict[str, Any], 
        law_source: LawSource,
        document: KnowledgeDocument
    ) -> LawArticle:
        """Create or update a law article from JSON data."""
        
        # Validate article data
        if not isinstance(article_data, dict):
            raise ValueError(f"Article data must be a dictionary, got {type(article_data)}")
        
        if 'text' not in article_data:
            raise ValueError("Article data must contain 'text' field")
        
        # Check if article already exists
        existing_article = await self.db.execute(
            select(LawArticle).where(
                LawArticle.law_source_id == law_source.id,
                LawArticle.article_number == article_data.get('article')
            )
        )
        existing_article = existing_article.scalar_one_or_none()
        
        if existing_article:
            # Update existing article
            existing_article.title = article_data.get('title')
            existing_article.content = article_data['text']
            existing_article.order_index = article_data.get('order_index', 0)
            existing_article.source_document_id = document.id
            existing_article.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(existing_article)
            
            logger.info(f"📝 Updated existing article: {existing_article.article_number}")
            return existing_article
        else:
            # Create new article
            new_article = LawArticle(
                law_source_id=law_source.id,
                article_number=article_data.get('article'),
                title=article_data.get('title'),
                content=article_data['text'],
                order_index=article_data.get('order_index', 0),
                source_document_id=document.id,
                ai_processed_at=datetime.utcnow()
            )
            
            self.db.add(new_article)
            await self.db.commit()
            await self.db.refresh(new_article)
            
            logger.info(f"✨ Created new article: {new_article.article_number}")
            return new_article
    
    async def _create_knowledge_chunks(
        self, 
        article: LawArticle, 
        law_source: LawSource,
        document: KnowledgeDocument
    ) -> List[KnowledgeChunkSummary]:
        """
        Create knowledge chunks from article content with dual database support.
        
        This method creates chunks and stores them in both SQL database and Chroma vectorstore
        with proper metadata synchronization, similar to optimized_knowledge_service.py
        """
        
        chunks_summary = []
        
        # Split article content into chunks
        content = article.content or ""
        if not content.strip():
            return chunks_summary
        
        # Use the text splitter from vectorstore manager
        text_chunks = self.dual_db_manager.text_splitter.split_text(content)
        
        # Prepare texts and metadatas for batch processing (like optimized_knowledge_service.py)
        texts = []
        metadatas = []
        sql_chunks = []
        
        for i, chunk_text in enumerate(text_chunks):
            # Calculate token count
            token_count = len(chunk_text.split())
            
            # Create chunk object for SQL database
            chunk = KnowledgeChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_text,
                tokens_count=token_count,
                law_source_id=law_source.id,
                article_id=article.id,
                order_index=i,
                verified_by_admin=False
            )
            
            # Prepare metadata for Chroma (similar to optimized_knowledge_service.py)
            chunk_metadata = {
                "article": article.article_number or "",
                "article_title": article.title or "",
                "law_name": law_source.name,
                "law_type": law_source.type,
                "jurisdiction": law_source.jurisdiction or "",
                "issuing_authority": law_source.issuing_authority or "",
                "issue_date": law_source.issue_date.isoformat() if law_source.issue_date else "",
                "document_title": document.title,
                "document_category": document.category,
                "keywords": [],  # Can be populated from article data if available
                "order_index": i
            }
            
            # Clean metadata for Chroma compatibility (like optimized_knowledge_service.py)
            clean_metadata = {}
            for key, value in chunk_metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    try:
                        clean_metadata[key] = ", ".join(map(str, value))
                    except Exception:
                        clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            texts.append(chunk_text)
            metadatas.append(clean_metadata)
            sql_chunks.append(chunk)
        
        # Batch process: Add all chunks to SQL first
        try:
            for chunk in sql_chunks:
                self.db.add(chunk)
            await self.db.commit()
            
            # Refresh all chunks to get their IDs
            for chunk in sql_chunks:
                await self.db.refresh(chunk)
            
            logger.info(f"✅ Added {len(sql_chunks)} chunks to SQL database")
            
        except Exception as sql_error:
            logger.error(f"❌ Failed to add chunks to SQL: {sql_error}")
            await self.db.rollback()
            return chunks_summary
        
        # Batch process: Add all chunks to Chroma (like optimized_knowledge_service.py)
        try:
            # Prepare IDs for Chroma (use SQL chunk IDs)
            chunk_ids = [str(chunk.id) for chunk in sql_chunks]
            
            # Add all chunks to Chroma at once
            self.dual_db_manager.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            # Persist Chroma changes
            self.dual_db_manager.vectorstore.persist()
            
            logger.info(f"✅ Added {len(texts)} chunks to Chroma vectorstore")
            
            # Create summaries for successful chunks
            for chunk in sql_chunks:
                chunks_summary.append(KnowledgeChunkSummary(
                    id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    tokens_count=chunk.tokens_count,
                    law_source_id=chunk.law_source_id,
                    article_id=chunk.article_id
                ))
            
        except Exception as chroma_error:
            logger.error(f"❌ Failed to add chunks to Chroma: {chroma_error}")
            # Rollback SQL changes if Chroma fails
            try:
                for chunk in sql_chunks:
                    await self.db.delete(chunk)
                await self.db.commit()
                logger.info("🔄 Rolled back SQL changes due to Chroma failure")
            except Exception as rollback_error:
                logger.error(f"❌ Failed to rollback SQL changes: {rollback_error}")
        
        logger.info(f"📦 Created {len(chunks_summary)} chunks for article {article.article_number}")
        return chunks_summary
    
    def _split_text_into_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > search_start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    # ===========================================
    # PLACEHOLDER METHODS FOR FUTURE FILE TYPES
    # ===========================================
    
    async def _parse_pdf_document(
        self, 
        file_path: str, 
        document: KnowledgeDocument,
        metadata: Dict[str, Any]
    ) -> Tuple[List[LawSourceSummary], List[LawArticleSummary], List[KnowledgeChunkSummary]]:
 
        logger.warning("📄 PDF parsing not yet implemented")
        raise NotImplementedError("PDF parsing will be implemented in future version")
    
    async def _parse_docx_document(
        self, 
        file_path: str, 
        document: KnowledgeDocument,
        metadata: Dict[str, Any]
    ) -> Tuple[List[LawSourceSummary], List[LawArticleSummary], List[KnowledgeChunkSummary]]:
     
        logger.warning("📝 DOCX parsing not yet implemented")
        raise NotImplementedError("DOCX parsing will be implemented in future version")
    
    async def _parse_txt_document(
        self, 
        file_path: str, 
        document: KnowledgeDocument,
        metadata: Dict[str, Any]
    ) -> Tuple[List[LawSourceSummary], List[LawArticleSummary], List[KnowledgeChunkSummary]]:
      
        logger.warning("📄 TXT parsing not yet implemented")
        raise NotImplementedError("TXT parsing will be implemented in future version")


class DocumentUploadService:
    """
    Enhanced service class for handling document upload operations with dual database support.
    
    This class orchestrates the entire upload process including:
    - File validation and storage
    - Duplicate detection
    - Document parsing with dual database synchronization
    - SQL and Chroma database operations
    - Response formatting
    - Error handling with rollback capabilities
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.parser = LegalDocumentParser(db_session)
        self.dual_db_manager = DualDatabaseManager(db_session)
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        title: str,
        category: str,
        uploaded_by: Optional[int] = None
    ) -> Dict[str, Any]:
    
        logger.info(f"🚀 Starting document upload: {filename}")
        
        try:
            # Step 1: Save file and calculate hash
            file_path, file_hash, file_size = await self._save_file_and_hash(file_content, filename)
            
            # Step 2: Check for duplicates
            duplicate_detected = await self._check_duplicate(file_hash)
            
            # Step 3: Create KnowledgeDocument record
            document = await self._create_document_record(
                title, category, file_path, file_hash, uploaded_by
            )
            
            # Step 4: Parse document content
            law_sources, articles, chunks = await self.parser.parse_document(
                file_path, document, {"filename": filename}
            )
            
            # Step 5: Update document status
            document.status = 'processed'
            document.processed_at = datetime.utcnow()
            await self.db.commit()
            
            # Step 6: Prepare response
            result = {
                "document_id": document.id,
                "title": document.title,
                "category": document.category,
                "file_path": document.file_path,
                "file_hash": document.file_hash,
                "status": document.status,
                "uploaded_at": document.uploaded_at,
                "chunks_created": len(chunks),
                "law_sources_processed": len(law_sources),
                "articles_processed": len(articles),
                "law_sources": [source.model_dump() for source in law_sources],
                "articles": [article.model_dump() for article in articles],
                "chunks": [chunk.model_dump() for chunk in chunks],
                "processing_time_seconds": 0.0,  # TODO: Implement timing
                "file_size_bytes": file_size,
                "duplicate_detected": duplicate_detected
            }
            
            logger.info(f"✅ Document upload completed: {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document upload failed: {e}")
            raise
    
    async def _save_file_and_hash(self, file_content: bytes, filename: str) -> Tuple[str, str, int]:
     
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = uploads_dir / safe_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
        
        logger.info(f"💾 File saved: {file_path} ({file_size} bytes, hash: {file_hash[:16]}...)")
        return str(file_path), file_hash, file_size
    
    async def _check_duplicate(self, file_hash: str) -> bool:
      
        
        existing_doc = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.file_hash == file_hash)
        )
        existing_doc = existing_doc.scalar_one_or_none()
        
        if existing_doc:
            logger.warning(f"⚠️ Duplicate file detected: {existing_doc.title}")
            return True
        
        return False
    
    async def _create_document_record(
        self,
        title: str,
        category: str,
        file_path: str,
        file_hash: str,
        uploaded_by: Optional[int]
    ) -> KnowledgeDocument:
      
        
        document = KnowledgeDocument(
            title=title,
            category=category,
            file_path=file_path,
            file_hash=file_hash,
            source_type='uploaded',
            status='raw',
            uploaded_by=uploaded_by,
            uploaded_at=datetime.utcnow(),
            document_metadata={"upload_method": "api_endpoint"}
        )
        
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        
        logger.info(f"📄 Created document record: {document.title} (ID: {document.id})")
        return document
    
    # ===========================================
    # DUAL DATABASE MANAGEMENT METHODS
    # ===========================================
    
    async def update_chunk_content(
        self,
        chunk_id: int,
        new_content: str,
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update chunk content in both SQL and Chroma databases.
        
        Args:
            chunk_id: ID of the chunk to update
            new_content: New content for the chunk
            new_metadata: Optional new metadata
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🔄 Updating chunk {chunk_id} in both databases")
        
        try:
            # Get current chunk from SQL
            chunk = await self.db.get(KnowledgeChunk, chunk_id)
            if not chunk:
                logger.error(f"❌ Chunk {chunk_id} not found")
                return False
            
            # Prepare metadata
            metadata = new_metadata or {}
            
            # Update in both databases
            success = await self.dual_db_manager.update_chunk_in_both_databases(
                chunk_id, new_content, metadata
            )
            
            if success:
                logger.info(f"✅ Chunk {chunk_id} updated successfully")
            else:
                logger.error(f"❌ Failed to update chunk {chunk_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating chunk {chunk_id}: {e}")
            return False
    
    async def delete_chunk(self, chunk_id: int) -> bool:
        """
        Delete chunk from both SQL and Chroma databases.
        
        Args:
            chunk_id: ID of the chunk to delete
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🗑️ Deleting chunk {chunk_id} from both databases")
        
        try:
            success = await self.dual_db_manager.delete_chunk_from_both_databases(chunk_id)
            
            if success:
                logger.info(f"✅ Chunk {chunk_id} deleted successfully")
            else:
                logger.error(f"❌ Failed to delete chunk {chunk_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting chunk {chunk_id}: {e}")
            return False
    
    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document and all its chunks from both databases.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🗑️ Deleting document {document_id} and all chunks from both databases")
        
        try:
            success = await self.dual_db_manager.delete_document_from_both_databases(document_id)
            
            if success:
                logger.info(f"✅ Document {document_id} and all chunks deleted successfully")
            else:
                logger.error(f"❌ Failed to delete document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting document {document_id}: {e}")
            return False
    
    async def sync_databases(self) -> Dict[str, Any]:
        """
        Synchronize SQL and Chroma databases.
        
        Returns:
            Dictionary with synchronization statistics
        """
        logger.info("🔄 Synchronizing SQL and Chroma databases")
        
        try:
            stats = await self.dual_db_manager.sync_database_states()
            
            logger.info(f"✅ Database synchronization completed: {stats}")
            return {
                "success": True,
                "message": "Database synchronization completed",
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"❌ Database synchronization failed: {e}")
            return {
                "success": False,
                "message": f"Database synchronization failed: {str(e)}",
                "stats": {}
            }
    
    async def get_database_status(self) -> Dict[str, Any]:
        """
        Get status of both SQL and Chroma databases.
        
        Returns:
            Dictionary with database status information
        """
        try:
            # Get SQL database status
            sql_stats = await self.db.execute(
                select(
                    func.count(KnowledgeDocument.id).label('documents'),
                    func.count(LawSource.id).label('law_sources'),
                    func.count(LawArticle.id).label('articles'),
                    func.count(KnowledgeChunk.id).label('chunks')
                )
            )
            sql_row = sql_stats.first()
            
            # Get Chroma database status
            chroma_collection = self.dual_db_manager.vectorstore._collection
            chroma_count = chroma_collection.count()
            
            return {
                "sql_database": {
                    "documents": sql_row.documents or 0,
                    "law_sources": sql_row.law_sources or 0,
                    "articles": sql_row.articles or 0,
                    "chunks": sql_row.chunks or 0
                },
                "chroma_database": {
                    "chunks": chroma_count
                },
                "synchronization": {
                    "sql_chunks": sql_row.chunks or 0,
                    "chroma_chunks": chroma_count,
                    "sync_status": "synchronized" if (sql_row.chunks or 0) == chroma_count else "out_of_sync"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get database status: {e}")
            return {
                "error": str(e),
                "sql_database": {},
                "chroma_database": {},
                "synchronization": {}
            }

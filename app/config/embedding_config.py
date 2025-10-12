"""
Embedding Configuration - Global settings for ML model usage

This module provides centralized configuration for embedding services
to control ML model loading and memory usage.
"""

import os
from typing import Optional

class EmbeddingConfig:
    """
    Global configuration for embedding services.
    
    Environment Variables:
    - DISABLE_ML_EMBEDDINGS: Set to 'true' to disable all ML model loading
    - EMBEDDING_MODEL: Override default model (e.g., 'no_ml', 'ultra_small')
    - FORCE_NO_ML_MODE: Force NO-ML mode regardless of other settings
    """
    
    @staticmethod
    def is_ml_disabled() -> bool:
        """
        Check if ML embeddings are disabled globally.
        
        Returns:
            True if ML should be disabled, False otherwise
        """
        # Check explicit disable flag
        if os.getenv('DISABLE_ML_EMBEDDINGS', 'false').lower() == 'true':
            return True
        
        # Check force NO-ML mode
        if os.getenv('FORCE_NO_ML_MODE', 'false').lower() == 'true':
            return True
        
        # Check if model is explicitly set to no_ml
        if os.getenv('EMBEDDING_MODEL', '').lower() == 'no_ml':
            return True
        
        return False
    
    @staticmethod
    def get_default_model() -> str:
        """
        Get the default model to use based on configuration.
        
        Returns:
            Model name (e.g., 'no_ml', 'ultra_small', 'sts-arabert')
        """
        # If ML is disabled, return no_ml
        if EmbeddingConfig.is_ml_disabled():
            return 'no_ml'
        
        # Check environment variable for custom model
        custom_model = os.getenv('EMBEDDING_MODEL')
        if custom_model:
            return custom_model
        
        # Default to NO-ML for safety (can be changed to 'ultra_small' if needed)
        return 'no_ml'
    
    @staticmethod
    def should_use_faiss() -> bool:
        """
        Check if FAISS indexing should be used.
        
        Returns:
            True if FAISS should be used, False otherwise
        """
        # Disable FAISS if ML is disabled (no embeddings to index)
        if EmbeddingConfig.is_ml_disabled():
            return False
        
        # Check environment variable
        use_faiss = os.getenv('USE_FAISS', 'false').lower()
        return use_faiss == 'true'
    
    @staticmethod
    def get_batch_size() -> int:
        """
        Get the batch size for embedding generation.
        
        Returns:
            Batch size (default: 2 for memory safety)
        """
        try:
            return int(os.getenv('EMBEDDING_BATCH_SIZE', '2'))
        except ValueError:
            return 2
    
    @staticmethod
    def get_max_seq_length() -> int:
        """
        Get the maximum sequence length for embeddings.
        
        Returns:
            Max sequence length (default: 256 for memory safety)
        """
        try:
            return int(os.getenv('EMBEDDING_MAX_SEQ_LENGTH', '256'))
        except ValueError:
            return 256
    
    @staticmethod
    def get_cache_size() -> int:
        """
        Get the embedding cache size.
        
        Returns:
            Cache size (default: 50 for memory safety)
        """
        try:
            return int(os.getenv('EMBEDDING_CACHE_SIZE', '50'))
        except ValueError:
            return 50
    
    @staticmethod
    def log_configuration():
        """Log the current embedding configuration."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info("🔧 Embedding Configuration:")
        logger.info(f"   ML Disabled: {EmbeddingConfig.is_ml_disabled()}")
        logger.info(f"   Default Model: {EmbeddingConfig.get_default_model()}")
        logger.info(f"   Use FAISS: {EmbeddingConfig.should_use_faiss()}")
        logger.info(f"   Batch Size: {EmbeddingConfig.get_batch_size()}")
        logger.info(f"   Max Seq Length: {EmbeddingConfig.get_max_seq_length()}")
        logger.info(f"   Cache Size: {EmbeddingConfig.get_cache_size()}")
        logger.info("=" * 60)


# Initialize configuration on import
# This will be logged when the module is first imported
import logging
logger = logging.getLogger(__name__)

# Set NO-ML mode as default for memory safety
os.environ.setdefault('DISABLE_ML_EMBEDDINGS', 'true')
os.environ.setdefault('EMBEDDING_MODEL', 'no_ml')
os.environ.setdefault('FORCE_NO_ML_MODE', 'true')

logger.info("🚫 Embedding config initialized with NO-ML MODE by default (for memory safety)")
logger.info("   To enable ML models, set DISABLE_ML_EMBEDDINGS=false in your environment")


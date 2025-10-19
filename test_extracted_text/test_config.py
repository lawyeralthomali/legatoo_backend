"""
Test the NO-ML configuration
"""

import os
import sys

# Set NO-ML mode
os.environ['DISABLE_ML_EMBEDDINGS'] = 'true'
os.environ['FORCE_NO_ML_MODE'] = 'true'

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.config.embedding_config import EmbeddingConfig
    
    print("=" * 60)
    print("NO-ML Configuration Test")
    print("=" * 60)
    
    print(f"ML Disabled: {EmbeddingConfig.is_ml_disabled()}")
    print(f"Default Model: {EmbeddingConfig.get_default_model()}")
    print(f"Use FAISS: {EmbeddingConfig.should_use_faiss()}")
    print(f"Batch Size: {EmbeddingConfig.get_batch_size()}")
    print(f"Max Seq Length: {EmbeddingConfig.get_max_seq_length()}")
    print(f"Cache Size: {EmbeddingConfig.get_cache_size()}")
    
    if EmbeddingConfig.is_ml_disabled() and EmbeddingConfig.get_default_model() == 'no_ml':
        print("\nSUCCESS: NO-ML mode is configured correctly!")
        print("The system will NOT load any ML models.")
        print("Hash-based embeddings will be used instead.")
        exit(0)
    else:
        print("\nWARNING: NO-ML mode may not be fully active")
        exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)


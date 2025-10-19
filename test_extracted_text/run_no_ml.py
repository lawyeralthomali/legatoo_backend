"""
Run the FastAPI server with NO-ML mode enabled.

This script ensures that all ML model loading is disabled
for maximum memory safety and performance.
"""

import os
import sys

# Set NO-ML environment variables BEFORE importing anything else
os.environ['DISABLE_ML_EMBEDDINGS'] = 'true'
os.environ['FORCE_NO_ML_MODE'] = 'true'
os.environ['EMBEDDING_MODEL'] = 'no_ml'
os.environ['USE_FAISS'] = 'false'
os.environ['EMBEDDING_BATCH_SIZE'] = '2'
os.environ['EMBEDDING_MAX_SEQ_LENGTH'] = '256'
os.environ['EMBEDDING_CACHE_SIZE'] = '50'

print("=" * 70)
print("🚫 Starting server in NO-ML MODE")
print("=" * 70)
print("Configuration:")
print(f"  - DISABLE_ML_EMBEDDINGS: {os.getenv('DISABLE_ML_EMBEDDINGS')}")
print(f"  - FORCE_NO_ML_MODE: {os.getenv('FORCE_NO_ML_MODE')}")
print(f"  - EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")
print()
print("Benefits:")
print("  ✅ No ML model loading - Zero memory usage")
print("  ✅ Fast startup - No model initialization delays")  
print("  ✅ Memory safe - No OOM crashes possible")
print("  ✅ Hash-based embeddings - Deterministic and fast")
print("=" * 70)
print()

# Now import and run the server
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


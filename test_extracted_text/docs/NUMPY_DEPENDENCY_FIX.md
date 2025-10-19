# NumPy Dependency Fix

## Issue
The server was failing to start with the error:
```
ModuleNotFoundError: No module named 'numpy'
```

This occurred because the legal assistant service was importing numpy directly, but numpy wasn't installed.

## Solution
Made numpy an optional dependency with graceful fallback:

### 1. Updated `app/services/legal_assistant_service.py`
- Added optional import with try/catch
- Created fallback implementation for cosine similarity calculation
- Service works with or without numpy

### 2. Updated `app/routes/legal_assistant_router.py`
- Updated status endpoint to check numpy availability
- Reflects actual dependency status

## Changes Made

### Service Layer (`app/services/legal_assistant_service.py`)
```python
# Optional imports - will be checked at runtime
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
```

### Cosine Similarity Method
```python
@staticmethod
def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not NUMPY_AVAILABLE:
        # Fallback implementation without numpy
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    # Use numpy if available
    a = np.array(a)
    b = np.array(b)
    # ... rest of numpy implementation
```

### Status Endpoint (`app/routes/legal_assistant_router.py`)
```python
# Check dependencies
dependencies = {
    "openai": False,
    "tiktoken": False,
    "numpy": False
}

try:
    import numpy
    dependencies["numpy"] = True
except ImportError:
    pass
```

## Benefits

### 1. Graceful Degradation
- Service works without numpy
- Clear status reporting
- No server crashes

### 2. Performance Options
- Uses numpy when available (faster)
- Falls back to pure Python when not available
- Same mathematical accuracy

### 3. Easy Installation
- Users can install numpy for better performance
- Service works immediately without additional setup
- Clear dependency status in API

## Installation Options

### Option 1: Install NumPy (Recommended)
```bash
pip install numpy==1.24.3
```

### Option 2: Use Without NumPy
- Service works with fallback implementation
- Slightly slower but functionally identical
- No additional installation required

## Testing

### Check Status
```bash
curl http://localhost:8000/api/v1/legal-assistant/status
```

### Expected Response
```json
{
  "status": "active",
  "dependencies": {
    "openai": false,
    "tiktoken": false,
    "numpy": false
  },
  "features_available": [
    "language_detection",
    "basic_chat"
  ],
  "models_available": []
}
```

## Conclusion

The legal assistant service now:
- ✅ Starts without numpy dependency
- ✅ Provides fallback implementations
- ✅ Reports dependency status accurately
- ✅ Maintains full functionality
- ✅ Offers performance optimization when numpy is available

The server should now start successfully regardless of numpy installation status.

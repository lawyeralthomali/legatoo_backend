#!/usr/bin/env python3
"""
Simple script to run the FastAPI application.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Bind to all interfaces to allow network access
        port=8000,
        reload=True,
        log_level="info"
    )

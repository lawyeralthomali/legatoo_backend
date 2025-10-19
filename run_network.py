#!/usr/bin/env python3
"""
Network-enabled script to run the FastAPI application on your specific IP.
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting FastAPI backend on network IP...")
    print("📡 Backend will be available at: http://192.168.100.13:8000")
    print("📖 API docs will be available at: http://192.168.100.13:8000/docs")
    print("🌐 CORS enabled for: http://192.168.100.13:3000 (Next.js frontend)")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="192.168.100.13",  # Your specific IP address
        port=8000,
        reload=True,
        log_level="info"
    )


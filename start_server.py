#!/usr/bin/env python3
"""
Startup script for the FastAPI application
This script starts the server on all network interfaces (0.0.0.0)
so it can be accessed from other devices on the network.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get the device's IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 60)
    print("🚀 Starting Supabase Auth FastAPI Server")
    print("=" * 60)
    print(f"📱 Device IP Address: {local_ip}")
    print(f"🌐 Server will be accessible at:")
    print(f"   • Local:    http://127.0.0.1:8000")
    print(f"   • Network:  http://{local_ip}:8000")
    print(f"   • External: http://0.0.0.0:8000")
    print("=" * 60)
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("🔍 Health Check: http://127.0.0.1:8000/health")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Bind to all interfaces
        port=8000,
        reload=True,     # Enable auto-reload for development
        log_level="info"
    )

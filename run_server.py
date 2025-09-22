#!/usr/bin/env python3
"""
Simple server startup script
"""

import os
import sys

# Set environment variables
os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im90aWl2ZWxmbHZpZGd5ZnNobWpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4NTQ2MDksImV4cCI6MjA2NzQzMDYwOX0.aoJZdCUfLngPLO0uDoYHp3GdiQpZlf5PlEZlr2BIr1h9c'
os.environ['SUPABASE_URL'] = 'https://otiivelflvidgyfshmjn.supabase.co'
os.environ['SUPABASE_JWT_SECRET'] = 'fHvCDR3sCJKCNYI0qsp34AolLlsolf5Zvow3NkQfZov/SZcP/5pUNBWExbLLbIfDCemnBZiMUTjv4vxurt/xCA=='

if __name__ == "__main__":
    try:
        import uvicorn
        print("🚀 Starting FastAPI server on all interfaces...")
        print("📱 Your device IP: 192.168.100.108")
        print("🌐 Access URLs:")
        print("   • Local:    http://127.0.0.1:8000")
        print("   • Network:  http://192.168.100.108:8000")
        print("📚 API Docs: http://127.0.0.1:8000/docs")
        print("=" * 50)
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models to ensure they are registered with SQLAlchemy
from .models import profile
from .models import plan
from .models import subscription_new
from .models import usage_tracking
from .models import billing
from .db.database import create_tables

# Import routers
from .routes.user_router import router as user_router
from .routes.profile_router import router as profile_router

from .routes.supabase_auth_router import router as supabase_auth_router
from .routes.subscription_router_new import router as subscription_router
from .routes.premium_router_new import router as premium_router

# Create FastAPI app
app = FastAPI(
    title="Supabase Auth FastAPI",
    description="A FastAPI backend integrated with Supabase Authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:8080",      # Vue dev server
        "http://127.0.0.1:3000",     # Local React
        "http://127.0.0.1:8080",     # Local Vue
        "http://192.168.100.108:3000", # Network React
        "http://192.168.100.108:8080", # Network Vue
        "http://192.168.100.108:8000", # Self-reference
        "http://localhost:8000",      # Self-reference local
        "http://127.0.0.1:8000",     # Self-reference local
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")

app.include_router(supabase_auth_router, prefix="/api/v1")
app.include_router(subscription_router, prefix="/api/v1")
app.include_router(premium_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    await create_tables()

@app.get("/")
async def root():
    """Root endpoint."""
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    return {
        "message": "Welcome to Supabase Auth FastAPI",
        "version": "1.0.0",
        "server_info": {
            "hostname": hostname,
            "local_ip": local_ip,
            "access_urls": {
                "local": "http://127.0.0.1:8000",
                "network": f"http://{local_ip}:8000",
                "docs": "http://127.0.0.1:8000/docs",
                "health": "http://127.0.0.1:8000/health"
            }
        },
        "endpoints": {
            "test_auth": "/api/v1/auth/login/mohammed",
            "real_auth": "/api/v1/supabase-auth/signin/mohammed",
            "signup": "/api/v1/supabase-auth/signup",
            "signin": "/api/v1/supabase-auth/signin",
            "current_user": "/api/v1/supabase-auth/user",
            "test_endpoints": "/api/v1/supabase-auth/test-endpoints",
            "profile": "/api/v1/profiles/me",
            "subscriptions": "/api/v1/subscriptions/status",
            "plans": "/api/v1/subscriptions/plans",
            "premium": "/api/v1/premium/status",
            "features": "/api/v1/premium/feature-limits"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "supabase-auth-fastapi"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

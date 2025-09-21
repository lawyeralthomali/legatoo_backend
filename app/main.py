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
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(subscription_router, prefix="/api/v1")
app.include_router(premium_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    await create_tables()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Supabase Auth FastAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/users/me",
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

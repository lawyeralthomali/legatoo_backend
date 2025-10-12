from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import uuid
import os

# Import models to ensure they are registered with SQLAlchemy
from .config.enhanced_logging import setup_logging, get_logger
from .config.embedding_config import EmbeddingConfig  # Import config EARLY
from .db.database import create_tables

# Import all models to ensure they are registered with SQLAlchemy before relationships are resolved
from .models import (
    User, Profile, RefreshToken,
    Subscription, Plan, Billing, UsageTracking, UserRole, Role,
    UserContract, UserFavorite, LawSource, LawBranch, LawChapter, LawArticle, LegalCase,
    CaseSection, LegalTerm, KnowledgeDocument, KnowledgeChunk,
    AnalysisResult, KnowledgeLink, KnowledgeMetadata
)

# Import routers
from .routes.profile_router import router as profile_router
from .routes.auth_routes import router as auth_routes
from .routes.user_routes import router as user_routes
from .routes.emergency_admin_routes import router as emergency_admin_routes

from .routes.subscription_router import router as subscription_router
from .routes.premium_router import router as premium_router
from .routes.categories_route import router as categories_router
from .routes.templates_route import router as templates_router
from .routes.user_contracts_router import router as user_contracts_router
from .routes.favorites_router import router as favorites_router
from .routes.legal_knowledge_router import router as legal_knowledge_router
from .routes.legal_laws_router import router as legal_laws_router
from .routes.legal_hierarchy_router import router as legal_hierarchy_router
from .routes.legal_cases_router import router as legal_cases_router
from .routes.chunk_processing_router import router as chunk_processing_router
from .routes.embedding_router import router as embedding_router
from .routes.search_router import router as search_router
from .routes.analysis_router import router as analysis_router
from .routes.rag_route import router as rag_router

from pydantic import BaseModel
from typing import List
# Import exception handlers
from .utils.exception_handlers import (
    app_exception_handler, validation_exception_handler,
    not_found_exception_handler, conflict_exception_handler,
    authentication_exception_handler, database_exception_handler,
    external_service_exception_handler, http_exception_handler,
    validation_error_handler, integrity_error_handler,
    sqlalchemy_error_handler, general_exception_handler
)
from .utils.exceptions import (
    AppException, ValidationException, NotFoundException,
    ConflictException, AuthenticationException, DatabaseException,
    ExternalServiceException
)
from .utils.api_exceptions import ApiException

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="SQLite Auth FastAPI",
    description="A FastAPI backend with SQLite authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
import os

# Get CORS origins from environment variable
cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

# Default origins for development
default_origins = [
    "http://localhost:3000",      # React dev server
    "http://localhost:8080",      # Vue dev server
    "http://127.0.0.1:3000",     # Local React
    "http://127.0.0.1:8080",     # Local Vue
    "http://192.168.100.108:3000", # Network React
    "http://192.168.100.108:8080", # Network Vue
    "http://192.168.100.108:8000", # Self-reference
    "http://192.168.100.109:3000", # Your frontend IP
    "http://192.168.100.109:8080", # Your frontend IP (Vue)
    "http://localhost:8000",      # Self-reference local
    "http://127.0.0.1:8000",     # Self-reference local
    "https://api.westlinktowing.com",
    "https://legatoo.westlinktowing.com",
]

# Use environment CORS origins if available, otherwise use defaults
if cors_origins and cors_origins[0]:
    # Filter out empty strings
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    allow_origins = cors_origins
else:
    # Production mode - allow common origins
    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://srv1022733.hstgr.cloud:8000",
        "https://srv1022733.hstgr.cloud:8000",
        "http://srv1022733.hstgr.cloud",
        "https://srv1022733.hstgr.cloud",
        "http://api.westlinktowing.com",
        "https://api.westlinktowing.com",
        "http://legatoo.westlinktowing.com",
        "https://legatoo.westlinktowing.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Mount static files for frontend pages
# This allows serving HTML files directly from the backend for testing
if os.path.exists("."):
    app.mount("/static", StaticFiles(directory="."), name="static")

# Add exception handlers
# Custom ApiException handler for standardized error responses
@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    """Handle ApiException with unified response format and logging."""
    logger = get_logger(__name__)
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    logger.error(f"ApiException [{correlation_id}]: {exc.payload}")
    return JSONResponse(status_code=exc.status_code, content=exc.payload)

# Enhanced HTTPException handler for dict details
@app.exception_handler(HTTPException)
async def enhanced_http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with unified response format and logging."""
    logger = get_logger(__name__)
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    
    # If someone raised HTTPException(detail=dict), return it as-is
    if isinstance(exc.detail, dict):
        logger.warning(f"HTTPException [{correlation_id}]: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    # Otherwise fallback to standard shape
    fallback = {
        "success": False,
        "message": exc.detail if isinstance(exc.detail, str) else "Bad Request",
        "data": None,
        "errors": [{"field": None, "message": exc.detail if isinstance(exc.detail, str) else "Bad Request"}]
    }
    logger.warning(f"HTTPException [{correlation_id}]: {fallback}")
    return JSONResponse(status_code=exc.status_code, content=fallback)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(ConflictException, conflict_exception_handler)
app.add_exception_handler(AuthenticationException, authentication_exception_handler)
app.add_exception_handler(DatabaseException, database_exception_handler)
app.add_exception_handler(ExternalServiceException, external_service_exception_handler)
# HTTPException handler is now handled by enhanced_http_exception_handler above
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(profile_router, prefix="/api/v1")
app.include_router(auth_routes)
app.include_router(user_routes, prefix="/api/v1")
app.include_router(emergency_admin_routes)  # Emergency admin routes
app.include_router(subscription_router, prefix="/api/v1")
app.include_router(premium_router, prefix="/api/v1")
app.include_router(categories_router)
app.include_router(templates_router)
app.include_router(user_contracts_router)
app.include_router(favorites_router)
app.include_router(legal_knowledge_router)  # Legal Knowledge Management
app.include_router(legal_laws_router)  # Legal Laws Management (New API)
app.include_router(legal_hierarchy_router)  # Legal Hierarchy CRUD (Branches, Chapters, Articles)
app.include_router(legal_cases_router)  # Legal Cases Ingestion Pipeline
app.include_router(chunk_processing_router)  # Chunk Processing with AI
app.include_router(embedding_router)  # Embeddings Service
app.include_router(search_router)     # Semantic Search Service
app.include_router(analysis_router)   # AI Legal Analysis Service (Gemini + RAG)
app.include_router(rag_router)        # RAG Service for Legal Laws

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    logger = get_logger("startup")
    logger.info("Starting application...")
    
    # Log embedding configuration
    EmbeddingConfig.log_configuration()
    
    await create_tables()
    logger.info("Application started successfully!")

@app.get("/")
async def root():
    """Root endpoint."""
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    return {
        "message": "Welcome to SQLite Auth FastAPI - 🎉 DEPLOYMENT TEST SUCCESS! 😊",
        "version": "1.0.0",
        "test_info": "🚀✨🎯 If you see this message, your deployment is working perfectly! 🎉",
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
            "signup": "/api/v1/auth/signup",
            "login": "/api/v1/auth/login",
            "refresh_token": "/api/v1/auth/refresh-token",
            "logout": "/api/v1/auth/logout",
            "profile": "/api/v1/profiles/me",
            "subscriptions": "/api/v1/subscriptions/status",
            "plans": "/api/v1/subscriptions/plans",
            "premium": "/api/v1/premium/status",
            "features": "/api/v1/premium/feature-limits",
            "categories": "/api/contracts/categories",
            "templates": "/api/contracts/templates",
            "user_contracts": "/api/contracts/user-contracts",
            "favorites": "/api/contracts/favorites",
            "legal_assistant": {
                "upload": "/api/v1/legal-assistant/documents/upload",
                "search": "/api/v1/legal-assistant/documents/search",
                "documents": "/api/v1/legal-assistant/documents",
                "statistics": "/api/v1/legal-assistant/statistics"
            },
            "legal_knowledge": {
                "law_sources": "/api/v1/legal-knowledge/law-sources",
                "law_articles": "/api/v1/legal-knowledge/law-articles",
                "legal_cases": "/api/v1/legal-knowledge/legal-cases",
                "legal_terms": "/api/v1/legal-knowledge/legal-terms",
                "knowledge_documents": "/api/v1/legal-knowledge/knowledge-documents",
                "analysis_results": "/api/v1/legal-knowledge/analysis-results",
                "unified_search": "/api/v1/legal-knowledge/search",
                "statistics": "/api/v1/legal-knowledge/stats"
            },
            "legal_laws": {
                "upload": "/api/v1/laws/upload",
                "upload_gemini_only": "/api/v1/laws/upload-gemini-only",
                "upload_json": "/api/v1/laws/upload-json",
                "list": "/api/v1/laws/",
                "get_tree": "/api/v1/laws/{law_id}/tree",
                "get_metadata": "/api/v1/laws/{law_id}",
                "update": "/api/v1/laws/{law_id}",
                "delete": "/api/v1/laws/{law_id}",
                "reparse": "/api/v1/laws/{law_id}/reparse",
                "analyze": "/api/v1/laws/{law_id}/analyze",
                "statistics": "/api/v1/laws/{law_id}/statistics"
            },
            "rag": {
                "upload": "/api/v1/rag/upload",
                "search": "/api/v1/rag/search",
                "status": "/api/v1/rag/status"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    import datetime
    return {
        "status": "healthy", 
        "service": "sqlite-auth-fastapi",
        "test_message": "🎉 Deployment Test SUCCESS! 😊",
        "emoji": "🚀✨🎯",
        "deployment_time": datetime.datetime.now().isoformat(),
        "message": "Hello from Legatoo Backend! If you see this, deployment is working perfectly! 🎉"
    }


@app.get("/test-deployment")
async def test_deployment():
    """Simple test endpoint to verify deployment is working."""
    import datetime
    import socket
    
    hostname = socket.gethostname()
    timestamp = datetime.datetime.now().isoformat()
    
    return {
        "status": "🎉 SUCCESS!",
        "message": "Hello from Legatoo Backend! 😊",
        "emoji": "🚀✨🎯",
        "deployment_info": {
            "hostname": hostname,
            "deployed_at": timestamp,
            "environment": "production",
            "server": "Hostinger VPS",
            "status": "Live and Running! 🟢"
        },
        "test_message": "If you can see this message, your deployment is working perfectly! 🎉",
        "next_steps": [
            "✅ Backend is deployed and running",
            "✅ API endpoints are accessible", 
            "✅ Ready for frontend integration",
            "🚀 Time to build amazing features!"
        ]
    }

@app.get("/debug-auth")
async def debug_auth():
    """Debug endpoint to test authentication service components."""
    import os
    from .services.auth_service import AuthService
    from .db.database import get_db_session
    from .config.urls import get_url_config
    
    try:
        # Test environment variables
        env_check = {
            "SECRET_KEY": bool(os.getenv("SECRET_KEY")),
            "JWT_SECRET": bool(os.getenv("JWT_SECRET")),
            "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "not_set"),
            "BACKEND_URL": os.getenv("BACKEND_URL", "not_set"),
        }
        
        # Test URL configuration
        url_config = get_url_config()
        url_config_info = {
            "environment": url_config.environment,
            "frontend_url": url_config.frontend_url,
            "backend_url": url_config.backend_url,
            "api_base_url": url_config.api_base_url,
            "email_base_url": url_config.email_base_url,
            "verification_url_example": url_config.get_verification_url("test-token"),
        }
        
        # Test database connection
        async with get_db_session() as db:
            auth_service = AuthService(db, "debug-test")
            
            # Test user repository
            test_email = "Ahmedkaml117m@gmail.com"
            user = await auth_service.user_repository.get_user_model_by_email(test_email)
            
            return {
                "status": "Debug Info",
                "environment_check": env_check,
                "url_configuration": url_config_info,
                "database_connection": "✅ Connected",
                "user_exists": user is not None,
                "user_email": test_email,
                "user_id": user.id if user else None,
                "user_verified": user.is_verified if user else None,
                "message": "Authentication service debug info"
            }
            
    except Exception as e:
        return {
            "status": "❌ Error",
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Debug endpoint failed - this shows the login issue"
        }


@app.get("/debug-urls")
async def debug_urls():
    """Debug endpoint to check URL configuration."""
    from .config.urls import get_url_config
    
    try:
        url_config = get_url_config()
        return {
            "status": "URL Configuration Debug",
            "environment": url_config.environment,
            "frontend_url": url_config.frontend_url,
            "backend_url": url_config.backend_url,
            "api_base_url": url_config.api_base_url,
            "email_base_url": url_config.email_base_url,
            "auth_urls": url_config.auth_urls,
            "email_urls": url_config.email_urls,
            "verification_url_example": url_config.get_verification_url("test-token-123"),
            "password_reset_url_example": url_config.get_password_reset_url("test-reset-token-456"),
            "message": "This shows the URL configuration used for email verification"
        }
    except Exception as e:
        return {
            "status": "❌ Error",
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Failed to load URL configuration"
        }


# Frontend HTML pages for testing
@app.get("/email-verification.html")
async def email_verification_page():
    """Serve email verification page."""
    if os.path.exists("email-verification.html"):
        return FileResponse("email-verification.html")
    else:
        raise HTTPException(status_code=404, detail="Email verification page not found")


@app.get("/login.html")
async def login_page():
    """Serve login page."""
    if os.path.exists("login.html"):
        return FileResponse("login.html")
    else:
        raise HTTPException(status_code=404, detail="Login page not found")


@app.get("/password-reset.html")
async def password_reset_page():
    """Serve password reset page."""
    if os.path.exists("password-reset.html"):
        return FileResponse("password-reset.html")
    else:
        raise HTTPException(status_code=404, detail="Password reset page not found")


@app.get("/app-config.js")
async def app_config_js():
    """Serve app configuration JavaScript file."""
    if os.path.exists("app-config.js"):
        return FileResponse("app-config.js", media_type="application/javascript")
    else:
        raise HTTPException(status_code=404, detail="App config file not found")


@app.get("/logo.png")
async def logo_png():
    """Serve logo image file."""
    if os.path.exists("logo.png"):
        return FileResponse("logo.png", media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Logo file not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

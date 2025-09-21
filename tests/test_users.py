import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
from app.api.users import User

# Test database URL (using SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Override the database dependency
async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
async def setup_database():
    """Set up test database before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to My Project API"}

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_register_user(setup_database):
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(setup_database):
    """Test registration with duplicate email."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # Register first user
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    # Try to register with same email
    user_data["username"] = "differentuser"
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_duplicate_username(setup_database):
    """Test registration with duplicate username."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # Register first user
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    # Try to register with same username
    user_data["email"] = "different@example.com"
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_user(setup_database):
    """Test user login."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # Register user
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    # Login user
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/users/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == login_data["username"]
    assert data["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_login_invalid_credentials(setup_database):
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/users/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_users(setup_database):
    """Test getting list of users."""
    # Register a user first
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    # Get users
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "testuser"

@pytest.mark.asyncio
async def test_get_user_by_id(setup_database):
    """Test getting user by ID."""
    # Register a user first
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Get user by ID
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "testuser"

@pytest.mark.asyncio
async def test_get_nonexistent_user(setup_database):
    """Test getting nonexistent user."""
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

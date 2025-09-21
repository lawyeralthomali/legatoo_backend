import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
from app.api.users import User
from app.models.item import Item

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

@pytest.fixture
async def test_user(setup_database):
    """Create a test user."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    return response.json()

# Note: These tests would need item endpoints to be implemented
# For now, they test the service functions directly

@pytest.mark.asyncio
async def test_create_item_service(setup_database, test_user):
    """Test item creation service."""
    from app.services.item_service import create_item
    from app.schemas.item import ItemCreate
    from app.db.database import AsyncSessionLocal
    
    item_data = ItemCreate(
        title="Test Item",
        description="A test item",
        price=19.99,
        is_available=True
    )
    
    async with AsyncSessionLocal() as db:
        item = await create_item(db, item_data, test_user["id"])
        assert item.title == "Test Item"
        assert item.price == 19.99
        assert item.owner_id == test_user["id"]

@pytest.mark.asyncio
async def test_get_item_by_id_service(setup_database, test_user):
    """Test getting item by ID service."""
    from app.services.item_service import create_item, get_item_by_id
    from app.schemas.item import ItemCreate
    from app.db.database import AsyncSessionLocal
    
    item_data = ItemCreate(
        title="Test Item",
        description="A test item",
        price=19.99,
        is_available=True
    )
    
    async with AsyncSessionLocal() as db:
        # Create item
        created_item = await create_item(db, item_data, test_user["id"])
        
        # Get item by ID
        retrieved_item = await get_item_by_id(db, created_item.id)
        assert retrieved_item is not None
        assert retrieved_item.title == "Test Item"
        assert retrieved_item.id == created_item.id

@pytest.mark.asyncio
async def test_get_items_service(setup_database, test_user):
    """Test getting list of items service."""
    from app.services.item_service import create_item, get_items
    from app.schemas.item import ItemCreate
    from app.db.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        # Create multiple items
        for i in range(3):
            item_data = ItemCreate(
                title=f"Test Item {i}",
                description=f"A test item {i}",
                price=19.99 + i,
                is_available=True
            )
            await create_item(db, item_data, test_user["id"])
        
        # Get all items
        items = await get_items(db)
        assert len(items) == 3

@pytest.mark.asyncio
async def test_update_item_service(setup_database, test_user):
    """Test updating item service."""
    from app.services.item_service import create_item, update_item, get_item_by_id
    from app.schemas.item import ItemCreate, ItemUpdate
    from app.db.database import AsyncSessionLocal
    
    item_data = ItemCreate(
        title="Test Item",
        description="A test item",
        price=19.99,
        is_available=True
    )
    
    update_data = ItemUpdate(
        title="Updated Item",
        price=29.99
    )
    
    async with AsyncSessionLocal() as db:
        # Create item
        created_item = await create_item(db, item_data, test_user["id"])
        
        # Update item
        updated_item = await update_item(db, created_item.id, update_data)
        assert updated_item is not None
        assert updated_item.title == "Updated Item"
        assert updated_item.price == 29.99
        assert updated_item.description == "A test item"  # Should remain unchanged

@pytest.mark.asyncio
async def test_delete_item_service(setup_database, test_user):
    """Test deleting item service."""
    from app.services.item_service import create_item, delete_item, get_item_by_id
    from app.schemas.item import ItemCreate
    from app.db.database import AsyncSessionLocal
    
    item_data = ItemCreate(
        title="Test Item",
        description="A test item",
        price=19.99,
        is_available=True
    )
    
    async with AsyncSessionLocal() as db:
        # Create item
        created_item = await create_item(db, item_data, test_user["id"])
        
        # Delete item
        success = await delete_item(db, created_item.id)
        assert success is True
        
        # Verify item is deleted
        deleted_item = await get_item_by_id(db, created_item.id)
        assert deleted_item is None

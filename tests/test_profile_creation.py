"""
Tests for profile creation utilities
"""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.utils.profile_creation import ensure_user_profile, create_profile_from_user_data
from app.schemas.profile import AccountTypeEnum


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def mock_profile_service():
    """Mock profile service"""
    service = AsyncMock()
    service.get_profile_by_id.return_value = None  # No existing profile
    service.create_profile.return_value = Mock(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number="+1234567890",
        account_type="personal"
    )
    return service


@pytest.mark.asyncio
async def test_ensure_user_profile_creates_new_profile(mock_db, mock_profile_service):
    """Test that ensure_user_profile creates a new profile when none exists"""
    user_id = uuid4()
    
    # Mock the ProfileService
    with pytest.mock.patch('app.utils.profile_creation.ProfileService', return_value=mock_profile_service):
        result = await ensure_user_profile(
            db=mock_db,
            user_id=user_id,
            first_name="John",
            last_name="Doe",
            phone_number="+1234567890"
        )
    
    assert result["created"] is True
    assert result["profile"] is not None
    assert "Profile created successfully" in result["message"]


@pytest.mark.asyncio
async def test_ensure_user_profile_uses_existing_profile(mock_db):
    """Test that ensure_user_profile returns existing profile when it exists"""
    user_id = uuid4()
    existing_profile = Mock(
        id=user_id,
        first_name="Existing",
        last_name="User",
        phone_number="+1234567890",
        account_type="personal"
    )
    
    # Mock ProfileService to return existing profile
    mock_service = AsyncMock()
    mock_service.get_profile_by_id.return_value = existing_profile
    mock_service.get_profile_response_by_id.return_value = existing_profile
    
    with pytest.mock.patch('app.utils.profile_creation.ProfileService', return_value=mock_service):
        result = await ensure_user_profile(
            db=mock_db,
            user_id=user_id,
            first_name="John",
            last_name="Doe"
        )
    
    assert result["created"] is False
    assert result["profile"] == existing_profile
    assert "Profile already exists" in result["message"]


@pytest.mark.asyncio
async def test_create_profile_from_user_data(mock_db):
    """Test creating profile from user metadata"""
    user_id = uuid4()
    user_metadata = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "+1234567890",
        "avatar_url": "https://example.com/avatar.jpg"
    }
    
    # Mock ProfileService
    mock_service = AsyncMock()
    mock_service.get_profile_by_id.return_value = None
    mock_service.create_profile.return_value = Mock(
        id=user_id,
        first_name="Jane",
        last_name="Smith",
        phone_number="+1234567890",
        account_type="personal"
    )
    
    with pytest.mock.patch('app.utils.profile_creation.ProfileService', return_value=mock_service):
        result = await create_profile_from_user_data(
            db=mock_db,
            user_id=user_id,
            user_metadata=user_metadata
        )
    
    assert result["created"] is True
    assert result["profile"] is not None
    assert result["profile"].first_name == "Jane"
    assert result["profile"].last_name == "Smith"


@pytest.mark.asyncio
async def test_ensure_user_profile_handles_creation_failure(mock_db):
    """Test that ensure_user_profile handles profile creation failures gracefully"""
    user_id = uuid4()
    
    # Mock ProfileService to raise exception
    mock_service = AsyncMock()
    mock_service.get_profile_by_id.return_value = None
    mock_service.create_profile.side_effect = Exception("Database error")
    
    with pytest.mock.patch('app.utils.profile_creation.ProfileService', return_value=mock_service):
        result = await ensure_user_profile(
            db=mock_db,
            user_id=user_id,
            first_name="John",
            last_name="Doe"
        )
    
    assert result["created"] is False
    assert result["profile"] is None
    assert "Failed to create profile" in result["message"]
    assert "error" in result

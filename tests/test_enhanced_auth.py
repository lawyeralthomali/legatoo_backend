"""
Comprehensive unit tests for enhanced authentication system.

This module tests all authentication features including JWT refresh flow,
brute force protection, email verification, and unified error handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.models.user import User
from app.models.profile import Profile
from app.models.refresh_token import RefreshToken
from app.schemas.request import SignupRequest, LoginRequest
from app.schemas.response import create_success_response
from app.utils.api_exceptions import ApiException


class TestAuthService:
    """Test cases for enhanced AuthService."""
    
    @pytest.fixture
    async def auth_service(self):
        """Create AuthService instance for testing."""
        db_mock = AsyncMock(spec=AsyncSession)
        return AuthService(db_mock, correlation_id="test-123")
    
    @pytest.fixture
    def signup_data(self):
        """Create valid signup data."""
        return SignupRequest(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            phone_number="0512345678"
        )
    
    @pytest.fixture
    def login_data(self):
        """Create valid login data."""
        return LoginRequest(
            email="test@example.com",
            password="TestPass123!"
        )
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.password_hash = "$2b$12$test_hash"
        user.is_active = True
        user.is_verified = True
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = None
        return user
    
    @pytest.fixture
    def mock_profile(self):
        """Create mock profile."""
        profile = Profile()
        profile.id = 1
        profile.user_id = 1
        profile.email = "test@example.com"
        profile.first_name = "Test"
        profile.last_name = "User"
        profile.phone_number = "0512345678"
        profile.account_type = "personal"
        return profile


class TestSignup(TestAuthService):
    """Test signup functionality."""
    
    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service, signup_data):
        """Test successful user signup."""
        # Mock database operations
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = None
        auth_service.db.flush = AsyncMock()
        auth_service.db.commit = AsyncMock()
        auth_service.db.refresh = AsyncMock()
        
        # Mock email service
        auth_service.email_service.send_verification_email = AsyncMock(return_value=True)
        
        result = await auth_service.signup(signup_data)
        
        assert result["success"] is True
        assert "verification_required" in result["data"]
        assert result["data"]["email"] == signup_data.email
        auth_service.db.add.assert_called()
        auth_service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, auth_service, signup_data):
        """Test signup with duplicate email."""
        # Mock existing user
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = User()
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.signup(signup_data)
        
        assert exc_info.value.status_code == 422
        assert "Email already registered" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_signup_weak_password(self, auth_service):
        """Test signup with weak password."""
        weak_signup_data = SignupRequest(
            email="test@example.com",
            password="weak",  # Too weak
            first_name="Test",
            last_name="User"
        )
        
        with pytest.raises(ValueError):
            await auth_service.signup(weak_signup_data)


class TestLogin(TestAuthService):
    """Test login functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, login_data, mock_user, mock_profile):
        """Test successful login."""
        # Mock database operations
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        auth_service.db.commit = AsyncMock()
        
        # Mock profile query
        profile_result = AsyncMock()
        profile_result.scalar_one_or_none.return_value = mock_profile
        auth_service.db.execute.side_effect = [AsyncMock(scalar_one_or_none=lambda: mock_user), profile_result]
        
        # Mock password verification
        auth_service.verify_password = MagicMock(return_value=True)
        
        # Mock refresh token creation
        auth_service.create_refresh_token_record = AsyncMock()
        
        result = await auth_service.login(login_data)
        
        assert result["success"] is True
        assert "access_token" in result["data"]
        assert "refresh_token" in result["data"]
        assert result["data"]["user"]["email"] == login_data.email
        auth_service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, login_data):
        """Test login with invalid credentials."""
        # Mock user not found
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.login(login_data)
        
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_login_account_locked(self, auth_service, login_data, mock_user):
        """Test login with locked account."""
        mock_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.login(login_data)
        
        assert exc_info.value.status_code == 429
        assert "temporarily locked" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_login_brute_force_protection(self, auth_service, login_data, mock_user):
        """Test brute force protection."""
        mock_user.failed_attempts = 4  # One less than max
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        auth_service.verify_password = MagicMock(return_value=False)
        auth_service.db.commit = AsyncMock()
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.login(login_data)
        
        assert exc_info.value.status_code == 401
        # Check that failed attempts were incremented
        assert mock_user.failed_attempts == 5
        auth_service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_unverified_email(self, auth_service, login_data, mock_user):
        """Test login with unverified email."""
        mock_user.is_verified = False
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        auth_service.verify_password = MagicMock(return_value=True)
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.login(login_data)
        
        assert exc_info.value.status_code == 401
        assert "not verified" in exc_info.value.payload["message"]


class TestRefreshToken(TestAuthService):
    """Test refresh token functionality."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user):
        """Test successful token refresh."""
        refresh_token = "valid_refresh_token"
        mock_refresh_token_record = RefreshToken()
        mock_refresh_token_record.user_id = 1
        mock_refresh_token_record.is_active = True
        mock_refresh_token_record.expires_at = datetime.utcnow() + timedelta(days=7)
        
        auth_service.validate_refresh_token = AsyncMock(return_value=mock_refresh_token_record)
        auth_service.get_user_by_id = AsyncMock(return_value=mock_user)
        
        result = await auth_service.refresh_token(refresh_token)
        
        assert result["success"] is True
        assert "access_token" in result["data"]
        assert result["data"]["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test refresh with invalid token."""
        refresh_token = "invalid_refresh_token"
        auth_service.validate_refresh_token = AsyncMock(return_value=None)
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.refresh_token(refresh_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired refresh token" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, auth_service):
        """Test refresh with expired token."""
        refresh_token = "expired_refresh_token"
        mock_refresh_token_record = RefreshToken()
        mock_refresh_token_record.expires_at = datetime.utcnow() - timedelta(days=1)
        
        auth_service.validate_refresh_token = AsyncMock(return_value=None)  # Expired tokens return None
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.refresh_token(refresh_token)
        
        assert exc_info.value.status_code == 401


class TestEmailVerification(TestAuthService):
    """Test email verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, mock_user):
        """Test successful email verification."""
        verification_token = "valid_token"
        mock_user.is_verified = False
        mock_user.verification_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.verify_email(verification_token)
        
        assert result["success"] is True
        assert result["data"]["verified"] is True
        assert mock_user.is_verified is True
        assert mock_user.verification_token is None
        auth_service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_service):
        """Test email verification with invalid token."""
        verification_token = "invalid_token"
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.verify_email(verification_token)
        
        assert exc_info.value.status_code == 400
        assert "Invalid verification token" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, auth_service, mock_user):
        """Test email verification with expired token."""
        verification_token = "expired_token"
        mock_user.verification_token_expires = datetime.utcnow() - timedelta(hours=1)
        
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.verify_email(verification_token)
        
        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.payload["message"]
    
    @pytest.mark.asyncio
    async def test_verify_email_already_verified(self, auth_service, mock_user):
        """Test email verification for already verified email."""
        verification_token = "already_verified_token"
        mock_user.is_verified = True
        
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.verify_email(verification_token)
        
        assert exc_info.value.status_code == 400
        assert "already verified" in exc_info.value.payload["message"]


class TestLogout(TestAuthService):
    """Test logout functionality."""
    
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service):
        """Test successful logout."""
        refresh_token = "valid_refresh_token"
        auth_service.revoke_refresh_token = AsyncMock(return_value=True)
        
        result = await auth_service.logout(refresh_token)
        
        assert result["success"] is True
        assert result["data"]["logout"] is True
        auth_service.revoke_refresh_token.assert_called_with(refresh_token)
    
    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, auth_service):
        """Test logout with invalid token."""
        refresh_token = "invalid_refresh_token"
        auth_service.revoke_refresh_token = AsyncMock(return_value=False)
        
        with pytest.raises(ApiException) as exc_info:
            await auth_service.logout(refresh_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.payload["message"]


class TestPasswordSecurity(TestAuthService):
    """Test password security features."""
    
    def test_password_hashing(self, auth_service):
        """Test password hashing."""
        password = "TestPass123!"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False
    
    def test_password_validation(self):
        """Test password validation in SignupRequest."""
        # Valid password
        valid_request = SignupRequest(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        assert valid_request.password == "TestPass123!"
        
        # Invalid passwords
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChars123"  # No special characters
        ]
        
        for invalid_password in invalid_passwords:
            with pytest.raises(ValueError):
                SignupRequest(
                    email="test@example.com",
                    password=invalid_password,
                    first_name="Test",
                    last_name="User"
                )


class TestTokenManagement(TestAuthService):
    """Test token management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_refresh_token_record(self, auth_service):
        """Test creating refresh token record."""
        user_id = 1
        token = "test_token"
        
        auth_service.db.add = MagicMock()
        auth_service.db.commit = AsyncMock()
        auth_service.db.refresh = AsyncMock()
        
        result = await auth_service.create_refresh_token_record(user_id, token)
        
        assert isinstance(result, RefreshToken)
        assert result.user_id == user_id
        assert result.is_active is True
        auth_service.db.add.assert_called()
        auth_service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_validate_refresh_token(self, auth_service):
        """Test refresh token validation."""
        token = "valid_token"
        mock_refresh_token = RefreshToken()
        mock_refresh_token.is_active = True
        mock_refresh_token.expires_at = datetime.utcnow() + timedelta(days=7)
        
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_refresh_token
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.validate_refresh_token(token)
        
        assert result == mock_refresh_token
        auth_service.db.commit.assert_called()  # Should update last_used_at
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self, auth_service):
        """Test refresh token revocation."""
        token = "token_to_revoke"
        mock_refresh_token = RefreshToken()
        mock_refresh_token.is_active = True
        
        auth_service.db.execute.return_value.scalar_one_or_none.return_value = mock_refresh_token
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.revoke_refresh_token(token)
        
        assert result is True
        assert mock_refresh_token.is_active is False
        auth_service.db.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

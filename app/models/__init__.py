# Models package
from ..db.database import Base
from .user import User
from .profile import Profile, AccountType
from .refresh_token import RefreshToken
from .legal_document import LegalDocument

# Import all models to ensure they are registered with SQLAlchemy
__all__ = ["Base", "User", "Profile", "AccountType", "RefreshToken", "LegalDocument"]









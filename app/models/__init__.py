# Models package
from ..db.database import Base
from .user import User
from .profile import Profile, AccountType
from .refresh_token import RefreshToken
from .legal_document2 import LegalDocument, LegalDocumentChunk, DocumentTypeEnum, LanguageEnum, ProcessingStatusEnum
from .subscription import Subscription, StatusType
from .plan import Plan
from .billing import Billing
from .usage_tracking import UsageTracking
from .role import UserRole, Role, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, DEFAULT_USER_ROLE, ROLE_HIERARCHY, get_role_level, has_permission
from .enjaz_account import EnjazAccount
from .case_imported import CaseImported
from .contract_category import ContractCategory
from .template import ContractTemplate
from .user_contract import UserContract
from .favorite import UserFavorite
from .legal_knowledge import (
    LawSource, LawBranch, LawChapter, LawArticle, LegalCase, CaseSection, LegalTerm,
    KnowledgeDocument, KnowledgeChunk, AnalysisResult, KnowledgeLink, KnowledgeMetadata
)

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Base", 
    "User", 
    "Profile", 
    "AccountType", 
    "RefreshToken", 
    "LegalDocument", 
    "LegalDocumentChunk", 
    "DocumentTypeEnum", 
    "LanguageEnum", 
    "ProcessingStatusEnum",
    "Subscription", 
    "StatusType",
    "Plan",
    "Billing",
    "UsageTracking",
    "UserRole", 
    "Role", 
    "ROLE_SUPER_ADMIN", 
    "ROLE_ADMIN", 
    "ROLE_USER", 
    "DEFAULT_USER_ROLE", 
    "ROLE_HIERARCHY", 
    "get_role_level", 
    "has_permission",
    "EnjazAccount",
    "CaseImported",
    "ContractCategory",
    "ContractTemplate", 
    "UserContract",
    "UserFavorite",
    # Legal Knowledge Models
    "LawSource",
    "LawBranch",
    "LawChapter",
    "LawArticle", 
    "LegalCase",
    "CaseSection",
    "LegalTerm",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "AnalysisResult",
    "KnowledgeLink",
    "KnowledgeMetadata"
]









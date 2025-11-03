# Models package
from ..db.database import Base
from .user import User
from .profile import Profile, AccountType
from .refresh_token import RefreshToken
from .subscription import Subscription, StatusType
from .plan import Plan
from .billing import Billing
from .usage_tracking import UsageTracking
from .role import UserRole, Role, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, DEFAULT_USER_ROLE, ROLE_HIERARCHY, get_role_level, has_permission
from .legal_knowledge import (
    LawSource, LawArticle, LegalCase, CaseSection, LegalTerm,
    KnowledgeDocument, KnowledgeChunk
)
from .query_log import QueryLog
from .case_analysis import CaseAnalysis
from .support_ticket import SupportTicket, TicketStatus, TicketPriority

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Base", 
    "User", 
    "Profile", 
    "AccountType", 
    "RefreshToken", 
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
    # Legal Knowledge Models
    "LawSource",
    "LawArticle", 
    "LegalCase",
    "CaseSection",
    "LegalTerm",
    "KnowledgeDocument",
    "KnowledgeChunk",
    # Query logging
    "QueryLog",
    # Case Analysis
    "CaseAnalysis",
    # Support Tickets
    "SupportTicket",
    "TicketStatus",
    "TicketPriority",
]









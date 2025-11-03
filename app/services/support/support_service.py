"""
Support Ticket Service.

Business logic for support ticket operations.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ...repositories.support_ticket_repository import SupportTicketRepository
from ...models.support_ticket import SupportTicket, TicketStatus, TicketPriority


class SupportService:
    """Service for support ticket operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SupportTicketRepository(db)
    
    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        description: str,
        category: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        attachments: Optional[List[str]] = None
    ) -> SupportTicket:
        """Create a new support ticket."""
        return await self.repository.create_ticket(
            user_id=user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            attachments=attachments
        )
    
    async def get_ticket(
        self,
        ticket_id: int,
        user_id: Optional[int] = None
    ) -> Optional[SupportTicket]:
        """Get a ticket by ID."""
        return await self.repository.get_ticket_by_id(ticket_id, user_id)
    
    async def get_user_tickets(
        self,
        user_id: int,
        status: Optional[TicketStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupportTicket]:
        """Get all tickets for a user."""
        return await self.repository.get_user_tickets(user_id, status, skip, limit)
    
    async def get_all_tickets(
        self,
        status: Optional[TicketStatus] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupportTicket]:
        """Get all tickets (admin only)."""
        return await self.repository.get_all_tickets(status, category, skip, limit)
    
    async def update_ticket(
        self,
        ticket_id: int,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        admin_response: Optional[str] = None,
        admin_id: Optional[int] = None
    ) -> Optional[SupportTicket]:
        """Update a support ticket."""
        return await self.repository.update_ticket(
            ticket_id=ticket_id,
            subject=subject,
            description=description,
            status=status,
            priority=priority,
            admin_response=admin_response,
            admin_id=admin_id
        )
    
    async def delete_ticket(
        self,
        ticket_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Delete a support ticket."""
        return await self.repository.delete_ticket(ticket_id, user_id)
    
    async def count_user_tickets(
        self,
        user_id: int,
        status: Optional[TicketStatus] = None
    ) -> int:
        """Count tickets for a user."""
        return await self.repository.count_user_tickets(user_id, status)


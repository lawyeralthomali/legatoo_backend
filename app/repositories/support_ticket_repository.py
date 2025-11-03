"""
Repository for Support Tickets.

Handles database operations for support tickets.
"""

from typing import List, Optional
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from ..models.support_ticket import SupportTicket, TicketStatus, TicketPriority
from ..models.profile import Profile


class SupportTicketRepository:
    """Repository for support ticket database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        attachments_json = json.dumps(attachments) if attachments else None
        
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status=TicketStatus.OPEN,
            attachments=attachments_json
        )
        
        try:
            self.db.add(ticket)
            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def get_ticket_by_id(
        self,
        ticket_id: int,
        user_id: Optional[int] = None
    ) -> Optional[SupportTicket]:
        """Get a ticket by ID, optionally filtered by user_id."""
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        
        if user_id:
            query = query.where(SupportTicket.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_tickets(
        self,
        user_id: int,
        status: Optional[TicketStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupportTicket]:
        """Get all tickets for a specific user."""
        query = select(SupportTicket).where(SupportTicket.user_id == user_id)
        
        if status:
            query = query.where(SupportTicket.status == status)
        
        query = query.order_by(desc(SupportTicket.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_tickets(
        self,
        status: Optional[TicketStatus] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupportTicket]:
        """Get all tickets (admin only)."""
        query = select(SupportTicket)
        
        if status:
            query = query.where(SupportTicket.status == status)
        
        if category:
            query = query.where(SupportTicket.category == category)
        
        query = query.order_by(desc(SupportTicket.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
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
        ticket = await self.get_ticket_by_id(ticket_id)
        
        if not ticket:
            return None
        
        if subject is not None:
            ticket.subject = subject
        if description is not None:
            ticket.description = description
        if status is not None:
            ticket.status = status
            if status == TicketStatus.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
        if priority is not None:
            ticket.priority = priority
        if admin_response is not None:
            ticket.admin_response = admin_response
        if admin_id is not None:
            ticket.admin_id = admin_id
        
        try:
            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def delete_ticket(self, ticket_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a support ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, user_id)
        
        if not ticket:
            return False
        
        try:
            await self.db.delete(ticket)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def count_user_tickets(
        self,
        user_id: int,
        status: Optional[TicketStatus] = None
    ) -> int:
        """Count tickets for a user."""
        from sqlalchemy import func
        
        query = select(func.count(SupportTicket.id)).where(SupportTicket.user_id == user_id)
        
        if status:
            query = query.where(SupportTicket.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0


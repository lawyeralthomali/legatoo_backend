"""
Billing Repository for data access operations.

This module handles all database operations related to billing/invoices,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from .base import BaseRepository
from ..models.billing import Billing


class BillingRepository(BaseRepository):
    """Repository for billing data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize billing repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Billing)
    
    async def create_invoice(
        self,
        subscription_id: UUID,
        amount: float,
        currency: str = 'SAR',
        payment_method: Optional[str] = None
    ) -> Billing:
        """
        Create a new invoice.
        
        Args:
            subscription_id: Subscription UUID
            amount: Invoice amount
            currency: Currency code
            payment_method: Payment method
            
        Returns:
            Created Billing model
        """
        invoice = Billing.create_invoice(
            subscription_id=str(subscription_id),
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )
        
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return invoice
    
    async def get_user_invoices(self, user_id: UUID) -> List[Billing]:
        """
        Get all invoices for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of Billing models ordered by date (newest first)
        """
        from ..models.subscription import Subscription
        
        result = await self.db.execute(
            select(Billing)
            .join(Subscription, Billing.subscription_id == Subscription.subscription_id)
            .where(Subscription.user_id == user_id)
            .order_by(Billing.invoice_date.desc())
        )
        return result.scalars().all()
    
    async def get_subscription_invoices(self, subscription_id: UUID) -> List[Billing]:
        """
        Get all invoices for a subscription.
        
        Args:
            subscription_id: Subscription UUID
            
        Returns:
            List of Billing models
        """
        result = await self.db.execute(
            select(Billing)
            .where(Billing.subscription_id == subscription_id)
            .order_by(Billing.invoice_date.desc())
        )
        return result.scalars().all()
    
    async def get_invoice_by_id(self, invoice_id: UUID) -> Optional[Billing]:
        """
        Get invoice by ID.
        
        Args:
            invoice_id: Invoice UUID
            
        Returns:
            Billing model if found, None otherwise
        """
        result = await self.db.execute(
            select(Billing).where(Billing.invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()
    
    async def mark_invoice_paid(self, invoice_id: UUID, payment_date: datetime) -> bool:
        """
        Mark invoice as paid.
        
        Args:
            invoice_id: Invoice UUID
            payment_date: Date payment was received
            
        Returns:
            True if updated, False if not found
        """
        invoice = await self.get_invoice_by_id(invoice_id)
        
        if not invoice:
            return False
        
        invoice.payment_status = 'paid'
        invoice.payment_date = payment_date
        await self.db.commit()
        
        return True


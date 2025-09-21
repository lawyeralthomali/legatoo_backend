from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db.database import Base


class Billing(Base):
    """Billing model for invoices and payments"""
    __tablename__ = "billing"

    invoice_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    subscription_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default='SAR')
    status = Column(String, nullable=False)  # paid, pending, failed, refunded
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    payment_method = Column(String, nullable=True)  # Card, Bank Transfer...

    # Relationships
    subscription = relationship("Subscription", back_populates="billing")

    def __repr__(self):
        return f"<Billing(invoice_id={self.invoice_id}, subscription_id={self.subscription_id}, amount={self.amount}, status='{self.status}')>"

    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid"""
        return self.status == 'paid'

    @property
    def is_pending(self) -> bool:
        """Check if invoice is pending"""
        return self.status == 'pending'

    @property
    def is_failed(self) -> bool:
        """Check if invoice payment failed"""
        return self.status == 'failed'

    @property
    def is_refunded(self) -> bool:
        """Check if invoice is refunded"""
        return self.status == 'refunded'

    def mark_paid(self, payment_method: str = None) -> None:
        """Mark invoice as paid"""
        self.status = 'paid'
        if payment_method:
            self.payment_method = payment_method

    def mark_failed(self) -> None:
        """Mark invoice as failed"""
        self.status = 'failed'

    def mark_refunded(self) -> None:
        """Mark invoice as refunded"""
        self.status = 'refunded'

    @classmethod
    def create_invoice(cls, subscription_id: str, amount: float, currency: str = 'SAR', payment_method: str = None) -> "Billing":
        """Create a new invoice"""
        return cls(
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status='pending',
            payment_method=payment_method
        )

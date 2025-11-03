from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, Field

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..services.support.support_service import SupportService
from ..models.support_ticket import TicketStatus, TicketPriority
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response
)


router = APIRouter(prefix="/support", tags=["support"])


def get_support_service(db: AsyncSession = Depends(get_db)) -> SupportService:
    """Dependency to get support service."""
    return SupportService(db)


class CreateTicketRequest(BaseModel):
    """Request schema for creating a support ticket."""
    subject: str = Field(..., min_length=3, max_length=500, description="Ticket subject")
    description: str = Field(..., min_length=10, description="Detailed description")
    category: str = Field(..., description="Ticket category (technical, billing, general, bug_report)")
    priority: str = Field(default="medium", description="Ticket priority (low, medium, high, urgent)")


class UpdateTicketRequest(BaseModel):
    """Request schema for updating a support ticket."""
    subject: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    status: Optional[str] = Field(None, description="Ticket status (open, in_progress, resolved, closed)")
    priority: Optional[str] = Field(None, description="Ticket priority (low, medium, high, urgent)")
    admin_response: Optional[str] = Field(None, description="Admin response to the ticket")


@router.post("/tickets", response_model=ApiResponse)
async def create_support_ticket(
    ticket_data: CreateTicketRequest,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Create a new support ticket."""
    try:
        # Get user profile ID
        from ..repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(support_service.db)
        profile = await profile_repo.get_by_user_id(current_user.sub)
        
        if not profile:
            return create_error_response(
                message="User profile not found",
                errors=[ErrorDetail(field="user", message="Profile does not exist")]
            )
        
        # Validate priority
        priority_map = {
            "low": TicketPriority.LOW,
            "medium": TicketPriority.MEDIUM,
            "high": TicketPriority.HIGH,
            "urgent": TicketPriority.URGENT
        }
        priority = priority_map.get(ticket_data.priority.lower(), TicketPriority.MEDIUM)
        
        # Create ticket
        ticket = await support_service.create_ticket(
            user_id=profile.id,
            subject=ticket_data.subject,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=priority
        )
        
        ticket_response = ticket.to_dict()
        
        return create_success_response(
            message="Support ticket created successfully",
            data=ticket_response
        )
    except Exception as e:
        return create_error_response(
            message="Failed to create support ticket",
            errors=[ErrorDetail(field="ticket", message=f"Internal server error: {str(e)}")]
        )


@router.get("/tickets", response_model=ApiResponse)
async def get_my_tickets(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Get current user's support tickets."""
    try:
        # Get user profile ID
        from ..repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(support_service.db)
        profile = await profile_repo.get_by_user_id(current_user.sub)
        
        if not profile:
            return create_error_response(
                message="User profile not found",
                errors=[ErrorDetail(field="user", message="Profile does not exist")]
            )
        
        # Parse status if provided
        ticket_status = None
        if status:
            status_map = {
                "open": TicketStatus.OPEN,
                "in_progress": TicketStatus.IN_PROGRESS,
                "resolved": TicketStatus.RESOLVED,
                "closed": TicketStatus.CLOSED
            }
            ticket_status = status_map.get(status.lower())
        
        # Get tickets
        tickets = await support_service.get_user_tickets(
            user_id=profile.id,
            status=ticket_status,
            skip=skip,
            limit=limit
        )
        
        tickets_data = [ticket.to_dict() for ticket in tickets]
        
        return create_success_response(
            message="Tickets retrieved successfully",
            data={"tickets": tickets_data, "count": len(tickets_data)}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve tickets",
            errors=[ErrorDetail(field="tickets", message=f"Internal server error: {str(e)}")]
        )


@router.get("/tickets/all", response_model=ApiResponse)
async def get_all_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Get all support tickets (admin only)."""
    try:
        # Check if user is admin
        if current_user.role not in ["admin", "super_admin"]:
            return create_error_response(
                message="Access denied",
                errors=[ErrorDetail(field="auth", message="Admin access required")]
            )
        
        # Parse status if provided
        ticket_status = None
        if status:
            status_map = {
                "open": TicketStatus.OPEN,
                "in_progress": TicketStatus.IN_PROGRESS,
                "resolved": TicketStatus.RESOLVED,
                "closed": TicketStatus.CLOSED
            }
            ticket_status = status_map.get(status.lower())
        
        # Get all tickets
        tickets = await support_service.get_all_tickets(
            status=ticket_status,
            category=category,
            skip=skip,
            limit=limit
        )
        
        tickets_data = [ticket.to_dict() for ticket in tickets]
        
        return create_success_response(
            message="All tickets retrieved successfully",
            data={"tickets": tickets_data, "count": len(tickets_data)}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve tickets",
            errors=[ErrorDetail(field="tickets", message=f"Internal server error: {str(e)}")]
        )


@router.get("/tickets/{ticket_id}", response_model=ApiResponse)
async def get_ticket(
    ticket_id: int,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Get a specific support ticket."""
    try:
        # Get user profile ID for authorization check
        from ..repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(support_service.db)
        profile = await profile_repo.get_by_user_id(current_user.sub)
        
        if not profile:
            return create_error_response(
                message="User profile not found",
                errors=[ErrorDetail(field="user", message="Profile does not exist")]
            )
        
        # Get ticket - restrict to user's own tickets unless admin
        user_id = None if current_user.role in ["admin", "super_admin"] else profile.id
        ticket = await support_service.get_ticket(ticket_id, user_id)
        
        if not ticket:
            return create_not_found_response(
                message="Ticket not found",
                errors=[ErrorDetail(field="ticket", message=f"Ticket with ID {ticket_id} not found")]
            )
        
        return create_success_response(
            message="Ticket retrieved successfully",
            data=ticket.to_dict()
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve ticket",
            errors=[ErrorDetail(field="ticket", message=f"Internal server error: {str(e)}")]
        )


@router.put("/tickets/{ticket_id}", response_model=ApiResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: UpdateTicketRequest,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Update a support ticket."""
    try:
        # Get user profile ID
        from ..repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(support_service.db)
        profile = await profile_repo.get_by_user_id(current_user.sub)
        
        if not profile:
            return create_error_response(
                message="User profile not found",
                errors=[ErrorDetail(field="user", message="Profile does not exist")]
            )
        
        # Check if user is super_admin for admin responses
        is_super_admin = current_user.role == "super_admin"
        is_admin = current_user.role in ["admin", "super_admin"]
        
        # Only super_admin can add admin responses
        if ticket_data.admin_response and not is_super_admin:
            return create_error_response(
                message="Access denied",
                errors=[ErrorDetail(field="auth", message="Only super admin can respond to tickets")]
            )
        
        # Get existing ticket
        user_id = None if is_admin else profile.id
        ticket = await support_service.get_ticket(ticket_id, user_id)
        
        if not ticket:
            return create_not_found_response(
                message="Ticket not found",
                errors=[ErrorDetail(field="ticket", message=f"Ticket with ID {ticket_id} not found")]
            )
        
        # Regular admins can only update their own tickets (subject, description)
        if not is_super_admin and ticket.user_id != profile.id:
            return create_error_response(
                message="Access denied",
                errors=[ErrorDetail(field="auth", message="You can only update your own tickets")]
            )
        
        # Parse status and priority if provided
        ticket_status = None
        if ticket_data.status:
            # Only super_admin can change status
            if not is_super_admin:
                return create_error_response(
                    message="Access denied",
                    errors=[ErrorDetail(field="auth", message="Only super admin can change ticket status")]
                )
            status_map = {
                "open": TicketStatus.OPEN,
                "in_progress": TicketStatus.IN_PROGRESS,
                "resolved": TicketStatus.RESOLVED,
                "closed": TicketStatus.CLOSED
            }
            ticket_status = status_map.get(ticket_data.status.lower())
        
        ticket_priority = None
        if ticket_data.priority:
            # Only super_admin can change priority
            if not is_super_admin:
                return create_error_response(
                    message="Access denied",
                    errors=[ErrorDetail(field="auth", message="Only super admin can change ticket priority")]
                )
            priority_map = {
                "low": TicketPriority.LOW,
                "medium": TicketPriority.MEDIUM,
                "high": TicketPriority.HIGH,
                "urgent": TicketPriority.URGENT
            }
            ticket_priority = priority_map.get(ticket_data.priority.lower())
        
        # Update ticket
        admin_id = profile.id if is_super_admin and ticket_data.admin_response else None
        
        updated_ticket = await support_service.update_ticket(
            ticket_id=ticket_id,
            subject=ticket_data.subject,
            description=ticket_data.description,
            status=ticket_status,
            priority=ticket_priority,
            admin_response=ticket_data.admin_response,
            admin_id=admin_id
        )
        
        if not updated_ticket:
            return create_error_response(
                message="Failed to update ticket",
                errors=[ErrorDetail(field="ticket", message="Could not update ticket")]
            )
        
        return create_success_response(
            message="Ticket updated successfully",
            data=updated_ticket.to_dict()
        )
    except Exception as e:
        return create_error_response(
            message="Failed to update ticket",
            errors=[ErrorDetail(field="ticket", message=f"Internal server error: {str(e)}")]
        )


@router.delete("/tickets/{ticket_id}", response_model=ApiResponse)
async def delete_ticket(
    ticket_id: int,
    current_user: TokenData = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
) -> ApiResponse:
    """Delete a support ticket."""
    try:
        # Get user profile ID
        from ..repositories.profile_repository import ProfileRepository
        profile_repo = ProfileRepository(support_service.db)
        profile = await profile_repo.get_by_user_id(current_user.sub)
        
        if not profile:
            return create_error_response(
                message="User profile not found",
                errors=[ErrorDetail(field="user", message="Profile does not exist")]
            )
        
        # Check authorization - users can only delete their own tickets
        is_admin = current_user.role in ["admin", "super_admin"]
        user_id = None if is_admin else profile.id
        
        success = await support_service.delete_ticket(ticket_id, user_id)
        
        if not success:
            return create_not_found_response(
                message="Ticket not found",
                errors=[ErrorDetail(field="ticket", message=f"Ticket with ID {ticket_id} not found")]
            )
        
        return create_success_response(
            message="Ticket deleted successfully",
            data={"ticket_id": ticket_id}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to delete ticket",
            errors=[ErrorDetail(field="ticket", message=f"Internal server error: {str(e)}")]
        )


from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from ..repositories.contract_template_repository import ContractTemplateRepository
from ..models.template import ContractTemplate
from ..schemas.template import TemplateCreate, TemplateUpdate
from ..utils.api_exceptions import ApiException


class ContractTemplateService:
    """Service for contract template business logic following SOLID principles."""
    
    def __init__(self):
        self.repository = ContractTemplateRepository()
    
    async def get_templates(
        self,
        db: AsyncSession,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_premium: Optional[bool] = None
    ) -> List[ContractTemplate]:
        """Get templates with filtering options."""
        return await self.repository.search_templates(
            db=db,
            search_term=search,
            category_id=category_id,
            is_featured=is_featured,
            is_premium=is_premium
        )
    
    async def get_template_by_id(
        self, 
        db: AsyncSession, 
        template_id: int
    ) -> ContractTemplate:
        """Get template by ID with validation and usage tracking."""
        template = await self.repository.get_by_id(db, template_id)
        if not template:
            raise ApiException(
                status_code=404,
                message="Template not found",
                errors=[{"field": "template_id", "message": "Template does not exist"}]
            )
        
        # Increment usage count
        await self.repository.increment_usage_count(db, template_id)
        
        return template
    
    async def create_template(
        self, 
        db: AsyncSession, 
        template_data: TemplateCreate,
        created_by: int
    ) -> ContractTemplate:
        """Create a new template with validation."""
        # Validate contract structure
        if not template_data.contract_structure:
            raise ApiException(
                status_code=400,
                message="Contract structure is required",
                errors=[{"field": "contract_structure", "message": "Template must have a valid structure"}]
            )
        
        # Create template (via repository)
        template_dict = template_data.dict()
        return await self.repository.create_template(db, template_dict, created_by)
    
    async def update_template(
        self, 
        db: AsyncSession, 
        template_id: int, 
        update_data: TemplateUpdate
    ) -> ContractTemplate:
        """Update template with validation."""
        # Validate template exists
        template = await self.repository.get_by_id(db, template_id)
        if not template:
            raise ApiException(
                status_code=404,
                message="Template not found",
                errors=[{"field": "template_id", "message": "Template does not exist"}]
            )
        
        # Update template (via repository)
        update_dict = update_data.dict(exclude_unset=True)
        updated_template = await self.repository.update_template(db, template_id, update_dict)
        
        if not updated_template:
            raise ApiException(
                status_code=500,
                message="Failed to update template",
                errors=[{"field": "template_id", "message": "Update operation failed"}]
            )
        
        return updated_template
    
    async def delete_template(
        self, 
        db: AsyncSession, 
        template_id: int
    ) -> bool:
        """Soft delete a template."""
        # Validate template exists first
        template = await self.repository.get_by_id(db, template_id)
        if not template:
            raise ApiException(
                status_code=404,
                message="Template not found",
                errors=[{"field": "template_id", "message": "Template does not exist"}]
            )
        
        # Soft delete (via repository)
        return await self.repository.soft_delete_template(db, template_id)
    
    async def get_featured_templates(
        self, 
        db: AsyncSession
    ) -> List[ContractTemplate]:
        """Get featured templates."""
        return await self.repository.get_featured_templates(db)
    
    async def get_premium_templates(
        self, 
        db: AsyncSession
    ) -> List[ContractTemplate]:
        """Get premium templates."""
        return await self.repository.get_premium_templates(db)
    
    async def get_free_templates(
        self, 
        db: AsyncSession
    ) -> List[ContractTemplate]:
        """Get free templates."""
        return await self.repository.get_free_templates(db)
    
    async def get_templates_by_category(
        self, 
        db: AsyncSession, 
        category_id: int
    ) -> List[ContractTemplate]:
        """Get templates by category."""
        return await self.repository.get_by_category_id(db, category_id)
    
    async def get_user_templates(
        self, 
        db: AsyncSession, 
        created_by: int
    ) -> List[ContractTemplate]:
        """Get templates created by a user."""
        return await self.repository.get_by_created_by(db, created_by)
    
    async def get_most_used_templates(
        self, 
        db: AsyncSession, 
        limit: int = 10
    ) -> List[ContractTemplate]:
        """Get most used templates."""
        return await self.repository.get_most_used_templates(db, limit)
    
    async def get_recent_templates(
        self, 
        db: AsyncSession, 
        limit: int = 10
    ) -> List[ContractTemplate]:
        """Get recently created templates."""
        return await self.repository.get_recent_templates(db, limit)
    
    async def update_template_rating(
        self, 
        db: AsyncSession, 
        template_id: int, 
        rating: int
    ) -> bool:
        """Update template rating."""
        if not 1 <= rating <= 5:
            raise ApiException(
                status_code=400,
                message="Invalid rating",
                errors=[{"field": "rating", "message": "Rating must be between 1 and 5"}]
            )
        
        return await self.repository.update_rating(db, template_id, rating)
    
    async def generate_contract_from_template(
        self, 
        db: AsyncSession, 
        template_id: int, 
        contract_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Generate a contract from a template."""
        # Get template (already uses repository)
        template = await self.get_template_by_id(db, template_id)
        
        # Validate contract data against template variables
        if template.variables_schema:
            self._validate_contract_data(contract_data, template.variables_schema)
        
        # Process template and generate final content
        final_content = self._process_template(template.contract_structure, contract_data)
        
        # Create user contract record (via repository)
        user_contract = await self.repository.create_user_contract_from_template(
            db=db,
            user_id=user_id,
            template_id=template_id,
            contract_data=contract_data,
            final_content=final_content
        )
        
        return {
            "user_contract_id": user_contract.user_contract_id,
            "final_content": final_content,
            "status": user_contract.status,
            "template_title": template.title_ar
        }
    
    def _validate_contract_data(
        self, 
        contract_data: Dict[str, Any], 
        variables_schema: Dict[str, Any]
    ) -> None:
        """Validate contract data against template variables schema."""
        required_fields = variables_schema.get("required", [])
        
        for field in required_fields:
            if field not in contract_data or not contract_data[field]:
                raise ApiException(
                    status_code=400,
                    message="Missing required field",
                    errors=[{"field": field, "message": f"Field '{field}' is required"}]
                )
    
    def _process_template(
        self, 
        contract_structure: Dict[str, Any], 
        contract_data: Dict[str, Any]
    ) -> str:
        """Process template structure and replace variables with actual data."""
        # This is a simplified implementation
        # In a real application, you would have more sophisticated template processing
        
        final_content = ""
        
        if "clauses" in contract_structure:
            for clause in contract_structure["clauses"]:
                clause_content = clause.get("content_ar", "")
                
                # Replace variables in the content
                for key, value in contract_data.items():
                    placeholder = f"{{{{{key}}}}}"
                    clause_content = clause_content.replace(placeholder, str(value))
                
                final_content += clause_content + "\n\n"
        
        return final_content.strip()

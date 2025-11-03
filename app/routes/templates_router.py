"""
Templates Router

API endpoints for contract template management and generation.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from ..db.database import get_db
from ..utils.auth import get_current_user_id
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..schemas.template_schemas import (
    TemplateVariablesResponse,
    GenerateContractRequest,
    GenerateContractResponse
)
from ..services.template_service import TemplateService
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/templates",
    tags=["Templates"]
)


@router.get("/", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    List all active templates.
    
    Returns templates with basic information for the templates library.
    """
    try:
        service = TemplateService(db)
        templates = await service.repository.get_active_templates()
        
        templates_data = []
        for template in templates:
            templates_data.append({
                "id": template.id,
                "title": template.title,
                "description": template.description,
                "category": template.category,
                "format": template.format,
                "is_premium": template.is_premium,
                "created_at": template.created_at.isoformat() if template.created_at else None,
            })
        
        return create_success_response(
            message="Templates retrieved successfully",
            data=templates_data
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve templates",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/{template_id}/variables", response_model=ApiResponse[TemplateVariablesResponse])
async def get_template_variables(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> ApiResponse[TemplateVariablesResponse]:
    """
    Get template variables schema for form generation.
    
    Returns metadata and variable definitions needed to render the form.
    """
    try:
        service = TemplateService(db)
        result = await service.get_template_variables(template_id)
        
        return create_success_response(
            message="Template variables retrieved successfully",
            data=result.dict()
        )
        
    except ValueError as e:
        logger.warning(f"Template not found: {template_id} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": "template_id", "message": str(e)}]
            }
        )
    except Exception as e:
        logger.error(f"Error getting template variables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve template variables",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.post("/{template_id}/generate", response_model=ApiResponse[GenerateContractResponse])
async def generate_contract(
    template_id: str,
    request: GenerateContractRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> ApiResponse[GenerateContractResponse]:
    """
    Generate a contract PDF from template and filled form data.
    
    Supports DOCX and HTML templates.
    Returns contract ID and PDF download URL.
    """
    try:
        service = TemplateService(db)
        result = await service.generate_contract(
            template_id=template_id,
            owner_id=current_user_id,
            filled_data=request.filled_data
        )
        
        return create_success_response(
            message="Contract generated successfully",
            data=result
        )
        
    except ValueError as e:
        logger.warning(f"Validation error generating contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )
    except RuntimeError as e:
        logger.error(f"Contract generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error generating contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to generate contract",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/{template_id}/preview")
async def preview_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Preview template with empty/placeholder values.
    
    Returns a PDF or HTML preview of the template showing its structure.
    """
    from fastapi.responses import FileResponse, Response
    import aiofiles
    
    try:
        service = TemplateService(db)
        preview_path = await service.preview_template(template_id)
        
        if not os.path.exists(preview_path):
            logger.error(f"Preview file not found at path: {preview_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": f"Preview file not found at: {preview_path}",
                    "data": None,
                    "errors": [{"field": None, "message": f"Preview file not found at: {preview_path}"}]
                }
            )
        
        # Determine media type based on file extension
        if preview_path.endswith('.pdf'):
            media_type = "application/pdf"
            filename = f"template_preview_{template_id}.pdf"
        elif preview_path.endswith('.html') or preview_path.endswith('.htm'):
            media_type = "text/html; charset=utf-8"
            filename = f"template_preview_{template_id}.html"
        elif preview_path.endswith('.docx'):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"template_preview_{template_id}.docx"
        else:
            media_type = "application/octet-stream"
            filename = f"template_preview_{template_id}"
        
        # Read file content based on file type
        if preview_path.endswith('.html') or preview_path.endswith('.htm'):
            # Read HTML as text with UTF-8 encoding
            async with aiofiles.open(preview_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            # Convert to bytes for Response
            content_bytes = content.encode('utf-8')
        else:
            # Read binary files (PDF, DOCX) as bytes
            async with aiofiles.open(preview_path, 'rb') as f:
                content_bytes = await f.read()
        
        # Return Response with inline Content-Disposition to display in browser
        return Response(
            content=content_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "no-cache"
            }
        )
        
    except ValueError as e:
        logger.warning(f"Template not found for preview: {template_id} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": "template_id", "message": str(e)}]
            }
        )
    except RuntimeError as e:
        logger.error(f"Error generating template preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error generating preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to generate template preview",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/contracts/{contract_id}/download")
async def download_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Download generated contract PDF.
    
    Validates user owns the contract before serving.
    """
    from fastapi.responses import FileResponse
    
    try:
        service = TemplateService(db)
        contract = await service.repository.get_contract_by_id(contract_id)
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        if contract.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not contract.pdf_path or not os.path.exists(contract.pdf_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract file not found"
            )
        
        return FileResponse(
            contract.pdf_path,
            media_type="application/pdf",
            filename=f"contract_{contract_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download contract"
        )


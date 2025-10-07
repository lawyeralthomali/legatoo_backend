"""
Adapter around existing HierarchicalDocumentProcessor to match parser interface.
"""

from typing import Dict, Any, Optional
from ..processors.hierarchical_document_processor import HierarchicalDocumentProcessor


class LocalParserAdapter:
    def __init__(self, processor: HierarchicalDocumentProcessor) -> None:
        self.processor = processor

    async def parse(self, file_path: str, law_source_details: Optional[Dict[str, Any]] = None, uploaded_by: Optional[int] = None, law_source_id: Optional[int] = None) -> Dict[str, Any]:
        result = await self.processor.process_document(
            file_path=file_path,
            law_source_details=law_source_details,
            uploaded_by=uploaded_by,
            law_source_id=law_source_id,
        )
        if not result.get("success"):
            return {"success": False, "message": result.get("message"), "data": None}

        structure = result.get("data", {}).get("structure")
        # Minimal normalization happens upstream in the service conversion step if needed
        return {"success": True, "message": "Local parsed", "data": {"structure": structure}}



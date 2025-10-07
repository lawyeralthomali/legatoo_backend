"""
Parser orchestrator: chooses AI or local parser with optional fallback.
"""

from typing import Dict, Any, Optional

from .ai_gemini_parser import GeminiParser
from .local_parser_adapter import LocalParserAdapter
from ..processors.hierarchical_document_processor import HierarchicalDocumentProcessor


class ParserOrchestrator:
    def __init__(self, processor: HierarchicalDocumentProcessor) -> None:
        self.ai = GeminiParser()
        self.local = LocalParserAdapter(processor)

    async def parse(
        self,
        file_path: str,
        law_source_details: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[int] = None,
        law_source_id: Optional[int] = None,
        use_ai: bool = True,
        fallback_on_failure: bool = True,
    ) -> Dict[str, Any]:
        if use_ai:
            ai_res = await self.ai.parse(file_path, law_source_details)
            if ai_res.get("success"):
                return {**ai_res, "parser_used": "gemini"}
            if not fallback_on_failure:
                return {**ai_res, "parser_used": "gemini"}
        # Local path
        local_res = await self.local.parse(file_path, law_source_details, uploaded_by, law_source_id)
        return {**local_res, "parser_used": "local"}



"""
AI Contract Generator Service

Generates professional legal contracts using Gemini AI from natural language
descriptions or structured data with placeholder replacement.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIContractGenerator:
    """
    Service for generating contracts using AI (Gemini or ChatGPT).
    Supports both natural language prompts and structured data inputs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI contract generator."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._model_name = "gemini-2.0-flash-exp"  # Default to Gemini
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AI client (Gemini preferred, fallback to OpenAI)."""
        # Try Gemini first
        try:
            from google import genai
            if os.getenv("GEMINI_API_KEY"):
                self._client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                self._model_name = "gemini-2.0-flash-exp"
                logger.info("✅ Gemini AI client initialized")
                return
        except ImportError:
            logger.warning("google-genai library not available")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
        
        # Fallback to OpenAI if Gemini not available
        try:
            import openai
            if os.getenv("OPENAI_API_KEY"):
                self._client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self._model_name = "gpt-4"
                logger.info("✅ OpenAI client initialized (fallback)")
                return
        except ImportError:
            logger.warning("openai library not available")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI: {e}")
        
        logger.error("❌ No AI client available. Please set GEMINI_API_KEY or OPENAI_API_KEY")
    
    async def generate_contract(
        self,
        prompt_text: str,
        category: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        language: str = "en",
        structured_data: Optional[Dict[str, Any]] = None,
        ai_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a contract from natural language prompt or structured data.
        
        Args:
            prompt_text: Natural language description of the contract
            category: Contract category (e.g., "Employment", "NDA")
            jurisdiction: Legal jurisdiction (e.g., "Saudi Arabia")
            language: Contract language (default: "en")
            structured_data: Dictionary of placeholders and values
            ai_model: Override AI model to use
            
        Returns:
            Dict with generated_content, ai_model, and metadata
        """
        if not self._client:
            raise ValueError("AI client not initialized. Set GEMINI_API_KEY or OPENAI_API_KEY")
        
        model_name = ai_model or self._model_name
        
        # Build the prompt
        system_prompt = self._build_system_prompt(category, jurisdiction, language)
        user_prompt = self._build_user_prompt(prompt_text, structured_data)
        
        try:
            if "gemini" in model_name.lower():
                generated_content = await self._generate_with_gemini(system_prompt, user_prompt, model_name)
            else:
                generated_content = await self._generate_with_openai(system_prompt, user_prompt, model_name)
            
            return {
                "success": True,
                "generated_content": generated_content,
                "ai_model": model_name,
                "created_at": datetime.utcnow(),
                "prompt_text": prompt_text
            }
        except Exception as e:
            logger.error(f"AI contract generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "generated_content": None,
                "ai_model": model_name
            }
    
    def _build_system_prompt(
        self,
        category: Optional[str],
        jurisdiction: Optional[str],
        language: str
    ) -> str:
        """Build system prompt with context."""
        prompt_parts = [
            "You are an expert legal contract generator. Your task is to create professional, ",
            "legally sound contracts based on user requirements.",
            "",
            "Requirements:",
            "- Generate clear, comprehensive contracts suitable for legal use",
            "- Include all standard clauses relevant to the contract type",
            "- Use professional legal language appropriate for the specified jurisdiction",
            "- Ensure the contract is complete and enforceable",
        ]
        
        if jurisdiction:
            prompt_parts.append(f"- Jurisdiction: {jurisdiction}")
        
        if category:
            prompt_parts.append(f"- Category: {category}")
        
        prompt_parts.extend([
            "",
            "Format the output as a clean, professional contract document.",
            "Do not include any explanations or meta-commentary, only the contract content.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(
        self,
        prompt_text: str,
        structured_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build user prompt with natural language and structured data."""
        parts = [f"Generate a contract based on the following description:\n\n{prompt_text}"]
        
        if structured_data:
            parts.append("\n\nAdditional details:")
            for key, value in structured_data.items():
                parts.append(f"- {key}: {value}")
            
            parts.append(
                "\n\nReplace any placeholders in the contract with the provided values. "
                "Use clear, consistent formatting for party names, dates, and other details."
            )
        
        return "\n".join(parts)
    
    async def _generate_with_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str
    ) -> str:
        """Generate contract using Gemini AI."""
        try:
            from google.genai import types
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call Gemini API
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model=model_name,
                    contents=full_prompt,
                    config={
                        "temperature": 0.3,  # Lower temperature for more consistent legal text
                        "max_output_tokens": 8000,
                        "top_p": 0.95
                    }
                ),
                timeout=120  # 2 minutes timeout
            )
            
            generated_text = getattr(response, "text", "")
            if not generated_text:
                raise ValueError("Empty response from Gemini AI")
            
            return generated_text.strip()
            
        except asyncio.TimeoutError:
            raise ValueError("AI generation timed out. Please try again with a shorter prompt.")
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    async def _generate_with_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str
    ) -> str:
        """Generate contract using OpenAI (GPT-4)."""
        try:
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                ),
                timeout=120
            )
            
            generated_text = response.choices[0].message.content
            if not generated_text:
                raise ValueError("Empty response from OpenAI")
            
            return generated_text.strip()
            
        except asyncio.TimeoutError:
            raise ValueError("AI generation timed out. Please try again with a shorter prompt.")
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def replace_placeholders(
        self,
        template_content: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Replace placeholders in template with actual values.
        
        Supports both {{placeholder}} and {placeholder} formats.
        
        Args:
            template_content: Template string with placeholders
            data: Dictionary of placeholder names and values
            
        Returns:
            Content with placeholders replaced
        """
        result = template_content
        
        # Replace {{placeholder}} format (double braces)
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        # Replace {placeholder} format (single braces)
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        
        return result

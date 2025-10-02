"""
Arabic Text Processing Utilities

This module provides utilities for handling Arabic text, including:
- RTL (Right-to-Left) text direction handling
- Arabic text normalization and reshaping
- Proper text formatting for display
- Bidirectional text processing
"""

import re
from typing import Optional, List
from unicodedata import normalize
import arabic_reshaper
from bidi.algorithm import get_display


class ArabicTextProcessor:
    """Utility class for processing Arabic text."""
    
    # Arabic Unicode ranges
    ARABIC_LETTERS = '\u0600-\u06FF'
    ARABIC_NUMBERS = '\u0660-\u0669'
    ARABIC_PUNCTUATION = '\u060C\u061B\u061F\u0640\u066A\u066B\u066C\u066D'
    
    @classmethod
    def is_arabic_text(cls, text: str) -> bool:
        """
        Check if text contains Arabic characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains Arabic characters
        """
        if not text:
            return False
        
        # Check for Arabic letters, numbers, or punctuation
        arabic_pattern = f'[{cls.ARABIC_LETTERS}{cls.ARABIC_NUMBERS}{cls.ARABIC_PUNCTUATION}]'
        return bool(re.search(arabic_pattern, text))
    
    @classmethod
    def normalize_arabic_text(cls, text: str) -> str:
        """
        Normalize Arabic text for better display.
        
        Args:
            text: Arabic text to normalize
            
        Returns:
            Normalized Arabic text
        """
        if not text:
            return text
        
        # Normalize Unicode
        text = normalize('NFC', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common Arabic text issues
        # Replace Arabic comma with regular comma
        text = text.replace('،', ',')
        
        # Fix Arabic quotation marks
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove extra dots and normalize punctuation
        text = re.sub(r'\.{2,}', '...', text)
        
        return text.strip()
    
    @classmethod
    def reshape_arabic_text(cls, text: str) -> str:
        """
        Reshape Arabic text to connect letters properly.
        
        This is crucial for Arabic text display as Arabic letters change shape
        based on their position in the word (isolated, initial, medial, final).
        
        Args:
            text: Arabic text to reshape
            
        Returns:
            Properly reshaped Arabic text
        """
        if not text or not cls.is_arabic_text(text):
            return text
        
        try:
            # Configure arabic_reshaper for better results
            config = arabic_reshaper.config_for_true_type_font('arial.ttf')
            reshaper = arabic_reshaper.ArabicReshaper(config)
            
            # Reshape the text
            reshaped = reshaper.reshape(text)
            return reshaped
        except Exception:
            # Fallback to default configuration
            try:
                reshaped = arabic_reshaper.reshape(text)
                return reshaped
            except Exception:
                # If reshaping fails, return original text
                return text
    
    @classmethod
    def process_bidirectional_text(cls, text: str) -> str:
        """
        Process text for proper bidirectional display.
        
        This ensures that Arabic text displays correctly in RTL context
        while preserving the order of numbers and symbols.
        
        Args:
            text: Text to process for bidirectional display
            
        Returns:
            Text processed for proper bidirectional display
        """
        if not text:
            return text
        
        try:
            # Use python-bidi to process bidirectional text
            processed = get_display(text)
            return processed
        except Exception:
            # If bidi processing fails, return original text
            return text
    
    @classmethod
    def preprocess_arabic_text(cls, text: str) -> str:
        """
        Complete Arabic text preprocessing pipeline.
        
        This method applies all necessary transformations:
        1. Normalize Unicode characters
        2. Reshape Arabic letters for proper connection
        3. Process bidirectional text for correct display
        
        Args:
            text: Raw Arabic text
            
        Returns:
            Fully processed Arabic text ready for display
        """
        if not text:
            return text
        
        # Step 1: Normalize the text
        normalized = cls.normalize_arabic_text(text)
        
        # Step 2: Reshape Arabic letters
        reshaped = cls.reshape_arabic_text(normalized)
        
        # Step 3: Process bidirectional text
        processed = cls.process_bidirectional_text(reshaped)
        
        return processed
    
    @classmethod
    def format_arabic_chunk(cls, content: str, language: str = "ar") -> dict:
        """
        Format Arabic chunk content with proper RTL handling.
        
        Args:
            content: Chunk content
            language: Document language
            
        Returns:
            Dictionary with formatted content and metadata
        """
        if not content:
            return {
                "content": content,
                "is_rtl": False,
                "language": language,
                "formatted_content": content
            }
        
        # Check if content is Arabic
        is_arabic = cls.is_arabic_text(content)
        
        # Process text based on language
        if is_arabic:
            # Apply complete Arabic preprocessing pipeline
            processed_content = cls.preprocess_arabic_text(content)
        else:
            # For non-Arabic text, just normalize
            processed_content = cls.normalize_arabic_text(content) if content else content
        
        # Create formatted content with RTL indicators
        if is_arabic:
            # Add RTL direction indicator with processed Arabic text
            formatted_content = f'<div dir="rtl" lang="ar" style="text-align: right; direction: rtl;">{processed_content}</div>'
        else:
            # Add LTR direction indicator
            formatted_content = f'<div dir="ltr" lang="{language}" style="text-align: left; direction: ltr;">{processed_content}</div>'
        
        return {
            "content": processed_content,
            "is_rtl": is_arabic,
            "language": language,
            "formatted_content": formatted_content,
            "original_content": content
        }
    
    @classmethod
    def extract_arabic_keywords(cls, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract Arabic keywords from text.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if not text or not cls.is_arabic_text(text):
            return []
        
        # Normalize text
        text = cls.normalize_arabic_text(text)
        
        # Remove punctuation and split into words
        words = re.findall(r'[\u0600-\u06FF]+', text)
        
        # Filter out very short words and common Arabic stop words
        stop_words = {
            'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'تلك', 'التي', 'الذي',
            'التي', 'الذين', 'اللاتي', 'اللائي', 'اللذان', 'اللتان', 'اللذين', 'اللتين',
            'هو', 'هي', 'هم', 'هن', 'أنت', 'أنت', 'أنتم', 'أنتن', 'أنا', 'نحن',
            'كان', 'كانت', 'كانوا', 'كن', 'يكون', 'تكون', 'يكونون', 'تكونون',
            'له', 'لها', 'لهم', 'لهن', 'له', 'لها', 'لهم', 'لهن'
        }
        
        # Filter words
        keywords = []
        for word in words:
            if len(word) >= 3 and word not in stop_words:
                keywords.append(word)
        
        # Remove duplicates and limit
        unique_keywords = list(dict.fromkeys(keywords))  # Preserves order
        return unique_keywords[:max_keywords]
    
    @classmethod
    def get_text_direction(cls, text: str) -> str:
        """
        Determine text direction based on content.
        
        Args:
            text: Text to analyze
            
        Returns:
            'rtl' for Arabic text, 'ltr' for other languages
        """
        return 'rtl' if cls.is_arabic_text(text) else 'ltr'

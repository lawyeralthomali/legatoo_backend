#!/usr/bin/env python3
"""
Script to convert Arabic article sections to numbers.
Reads JSON files containing legal articles and converts Arabic article names to numeric format.
"""

import json
import re
from typing import Dict, List, Any
import argparse
import os


class ArabicNumberConverter:
    """Converts Arabic text numbers to numeric values."""
    
    # Arabic number words mapping
    ARABIC_NUMBERS = {
        # Basic numbers
        'صفر': 0, 'أول': 1, 'ثاني': 2, 'ثالث': 3, 'رابع': 4, 'خامس': 5,
        'سادس': 6, 'سابع': 7, 'ثامن': 8, 'تاسع': 9, 'عاشر': 10,
        'حادي عشر': 11, 'ثاني عشر': 12, 'ثالث عشر': 13, 'رابع عشر': 14,
        'خامس عشر': 15, 'سادس عشر': 16, 'سابع عشر': 17, 'ثامن عشر': 18,
        'تاسع عشر': 19, 'عشرون': 20,
        
        # Tens
        'عشر': 10, 'عشرين': 20, 'ثلاثين': 30, 'أربعين': 40, 'خمسين': 50,
        'ستين': 60, 'سبعين': 70, 'ثمانين': 80, 'تسعين': 90,
        
        # Hundreds
        'مئة': 100, 'مائة': 100, 'مئتين': 200, 'ثلاثمئة': 300,
        'أربعمئة': 400, 'خمسمئة': 500, 'ستمئة': 600, 'سبعمئة': 700,
        'ثمانمئة': 800, 'تسعمئة': 900,
        
        # Thousands
        'ألف': 1000, 'ألفين': 2000, 'ثلاثة آلاف': 3000, 'أربعة آلاف': 4000,
        'خمسة آلاف': 5000, 'ستة آلاف': 6000, 'سبعة آلاف': 7000,
        'ثمانية آلاف': 8000, 'تسعة آلاف': 9000,
    }
    
    # Special cases for compound numbers
    COMPOUND_PATTERNS = [
        (r'ال(\w+) وال(\w+)', r'\1 و \2'),  # Handle "وال" conjunction
        (r'(\w+) و(\w+)', r'\1 \2'),        # Handle "و" conjunction
    ]
    
    def __init__(self):
        self._build_reverse_mapping()
    
    def _build_reverse_mapping(self):
        """Build reverse mapping for better lookup."""
        self.number_to_arabic = {v: k for k, v in self.ARABIC_NUMBERS.items()}
    
    def convert_arabic_to_number(self, text: str) -> int:
        """
        Convert Arabic text to number.
        
        Args:
            text: Arabic text containing numbers
            
        Returns:
            Numeric value
        """
        if not text or not text.strip():
            return 0
            
        text = text.strip().lower()
        
        # Handle special cases first
        if 'أول' in text and 'حادي' not in text:
            return 1
        if 'ثاني' in text and 'حادي' not in text:
            return 2
        if 'ثالث' in text:
            return 3
        if 'رابع' in text:
            return 4
        if 'خامس' in text:
            return 5
        if 'سادس' in text:
            return 6
        if 'سابع' in text:
            return 7
        if 'ثامن' in text:
            return 8
        if 'تاسع' in text:
            return 9
        if 'عاشر' in text:
            return 10
            
        # Handle compound numbers (like خمسة وعشرون = 25)
        if 'و' in text:
            parts = text.split('و')
            if len(parts) == 2:
                part1 = parts[0].strip()
                part2 = parts[1].strip()
                
                # Handle cases like "الخامسة والعشرون"
                if part1.endswith('ة'):
                    part1 = part1[:-1]  # Remove feminine suffix
                if part2.endswith('ة'):
                    part2 = part2[:-1]
                    
                num1 = self._get_basic_number(part1)
                num2 = self._get_basic_number(part2)
                
                if num1 and num2:
                    return num1 + num2
        
        # Handle single numbers
        return self._get_basic_number(text)
    
    def _get_basic_number(self, text: str) -> int:
        """Get basic number from text."""
        text = text.strip()
        
        # Direct mapping
        if text in self.ARABIC_NUMBERS:
            return self.ARABIC_NUMBERS[text]
        
        # Handle variations
        if 'حادي' in text:
            if 'عشر' in text:
                return 11
            return 1
        if 'ثاني' in text:
            if 'عشر' in text:
                return 12
            return 2
        if 'ثالث' in text:
            if 'عشر' in text:
                return 13
            return 3
        if 'رابع' in text:
            if 'عشر' in text:
                return 14
            return 4
        if 'خامس' in text:
            if 'عشر' in text:
                return 15
            return 5
        if 'سادس' in text:
            if 'عشر' in text:
                return 16
            return 6
        if 'سابع' in text:
            if 'عشر' in text:
                return 17
            return 7
        if 'ثامن' in text:
            if 'عشر' in text:
                return 18
            return 8
        if 'تاسع' in text:
            if 'عشر' in text:
                return 19
            return 9
            
        return 0


def extract_article_number(article_text: str) -> int:
    """
    Extract article number from Arabic article text.
    
    Args:
        article_text: Arabic text like "المادة الأولى", "المادة الخامسة والعشرون"
        
    Returns:
        Article number as integer
    """
    # Remove "المادة" prefix
    text = re.sub(r'^المادة\s*', '', article_text.strip())
    
    # Remove "مكرر" suffix if present
    text = re.sub(r'\s*مكرر\s*$', '', text.strip())
    
    converter = ArabicNumberConverter()
    return converter.convert_arabic_to_number(text)


def process_json_file(input_file: str, output_file: str = None) -> Dict[str, Any]:
    """
    Process JSON file and convert article names to numbers.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file (optional)
        
    Returns:
        Dictionary with processing results
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of articles")
    
    processed_data = []
    conversion_stats = {
        'total_articles': len(data),
        'successful_conversions': 0,
        'failed_conversions': 0,
        'conversion_errors': []
    }
    
    for i, article in enumerate(data):
        if not isinstance(article, dict) or 'article' not in article:
            conversion_stats['conversion_errors'].append(f"Article {i+1}: Invalid format")
            continue
            
        article_text = article['article']
        article_number = extract_article_number(article_text)
        
        if article_number > 0:
            # Create new article entry with numeric format
            new_article = article.copy()
            new_article['article_number'] = article_number
            new_article['article_arabic'] = article_text
            new_article['article'] = f"المادة {article_number}"
            
            processed_data.append(new_article)
            conversion_stats['successful_conversions'] += 1
        else:
            # Keep original if conversion failed
            processed_data.append(article)
            conversion_stats['failed_conversions'] += 1
            conversion_stats['conversion_errors'].append(f"Article {i+1}: '{article_text}' -> Could not convert")
    
    # Write output file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    return {
        'processed_data': processed_data,
        'stats': conversion_stats,
        'output_file': output_file
    }


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description='Convert Arabic article sections to numbers in JSON files'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file containing articles'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output JSON file (default: input_file with _numbered suffix)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show conversion statistics, do not create output file'
    )
    
    args = parser.parse_args()
    
    try:
        # Determine output file
        output_file = args.output
        if not output_file and not args.stats_only:
            base_name = os.path.splitext(args.input_file)[0]
            output_file = f"{base_name}_numbered.json"
        
        # Process the file
        result = process_json_file(args.input_file, output_file)
        stats = result['stats']
        
        # Print statistics
        print(f"\n📊 Conversion Statistics:")
        print(f"Total articles: {stats['total_articles']}")
        print(f"Successful conversions: {stats['successful_conversions']}")
        print(f"Failed conversions: {stats['failed_conversions']}")
        
        if stats['conversion_errors']:
            print(f"\n❌ Conversion Errors:")
            for error in stats['conversion_errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['conversion_errors']) > 10:
                print(f"  ... and {len(stats['conversion_errors']) - 10} more errors")
        
        if output_file and not args.stats_only:
            print(f"\n✅ Output written to: {output_file}")
            
        # Show sample of converted articles
        if result['processed_data']:
            print(f"\n📝 Sample of converted articles:")
            for i, article in enumerate(result['processed_data'][:5]):
                if 'article_number' in article:
                    print(f"  {article['article_number']}: {article['article']}")
            if len(result['processed_data']) > 5:
                print(f"  ... and {len(result['processed_data']) - 5} more articles")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


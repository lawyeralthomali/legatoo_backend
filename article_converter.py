#!/usr/bin/env python3
"""
Arabic Article Number Converter
Converts Arabic legal article names to numeric format.
"""

import json
import re
import argparse
import os


class ArabicArticleConverter:
    """Converts Arabic article names to numbers."""
    
    def __init__(self):
        # Arabic number words mapping
        self.numbers = {
            # Basic numbers
            'أول': 1, 'ثاني': 2, 'ثالث': 3, 'رابع': 4, 'خامس': 5,
            'سادس': 6, 'سابع': 7, 'ثامن': 8, 'تاسع': 9, 'عاشر': 10,
            
            # Teens
            'حادي عشر': 11, 'ثاني عشر': 12, 'ثالث عشر': 13, 'رابع عشر': 14,
            'خامس عشر': 15, 'سادس عشر': 16, 'سابع عشر': 17, 'ثامن عشر': 18,
            'تاسع عشر': 19,
            
            # Tens
            'عشرون': 20, 'ثلاثون': 30, 'أربعون': 40, 'خمسون': 50,
            'ستون': 60, 'سبعون': 70, 'ثمانون': 80, 'تسعون': 90,
            
            # Hundreds
            'مئة': 100, 'مائة': 100,
        }
    
    def extract_number(self, text):
        """Extract number from Arabic article text."""
        if not text:
            return 0
            
        # Remove "المادة" prefix and clean text
        text = re.sub(r'^المادة\s*', '', text.strip())
        text = re.sub(r'\s*مكرر\s*$', '', text)  # Remove "مكرر" suffix
        
        # Handle "بعد المائة" (after hundred)
        if 'بعد المائة' in text:
            base_text = text.replace('بعد المائة', '').strip()
            base_number = self._parse_base_number(base_text)
            return 100 + base_number if base_number > 0 else 0
        
        return self._parse_base_number(text)
    
    def _parse_base_number(self, text):
        """Parse base number from text."""
        text = text.strip()
        
        # Direct mapping
        if text in self.numbers:
            return self.numbers[text]
        
        # Handle compound numbers (like خمسة وعشرون = 25)
        if 'و' in text:
            return self._parse_compound_number(text)
        
        # Handle individual numbers
        return self._parse_single_number(text)
    
    def _parse_compound_number(self, text):
        """Parse compound numbers like خمسة وعشرون."""
        parts = text.split('و')
        if len(parts) != 2:
            return 0
            
        part1 = parts[0].strip()
        part2 = parts[1].strip()
        
        # Remove feminine suffixes
        if part1.endswith('ة'):
            part1 = part1[:-1]
        if part2.endswith('ة'):
            part2 = part2[:-1]
        
        # Handle combinations
        if part2 == 'عشرون':
            if part1 == 'خمس':
                return 25
            elif part1 == 'ست':
                return 26
            elif part1 == 'سبع':
                return 27
            elif part1 == 'ثمان':
                return 28
            elif part1 == 'تسع':
                return 29
            elif part1 == 'ثاني':
                return 22
            elif part1 == 'ثالث':
                return 23
            elif part1 == 'رابع':
                return 24
            elif part1 == 'أول':
                return 21
                
        elif part2 == 'ثلاثون':
            if part1 == 'أول':
                return 31
            elif part1 == 'ثاني':
                return 32
            elif part1 == 'ثالث':
                return 33
            elif part1 == 'رابع':
                return 34
            elif part1 == 'خمس':
                return 35
            elif part1 == 'ست':
                return 36
            elif part1 == 'سبع':
                return 37
            elif part1 == 'ثمان':
                return 38
            elif part1 == 'تسع':
                return 39
                
        elif part2 == 'أربعون':
            if part1 == 'أول':
                return 41
            elif part1 == 'ثاني':
                return 42
            elif part1 == 'ثالث':
                return 43
            elif part1 == 'رابع':
                return 44
            elif part1 == 'خمس':
                return 45
            elif part1 == 'ست':
                return 46
            elif part1 == 'سبع':
                return 47
            elif part1 == 'ثمان':
                return 48
            elif part1 == 'تسع':
                return 49
                
        elif part2 == 'خمسون':
            if part1 == 'أول':
                return 51
            elif part1 == 'ثاني':
                return 52
            elif part1 == 'ثالث':
                return 53
            elif part1 == 'رابع':
                return 54
            elif part1 == 'خمس':
                return 55
            elif part1 == 'ست':
                return 56
            elif part1 == 'سبع':
                return 57
            elif part1 == 'ثمان':
                return 58
            elif part1 == 'تسع':
                return 59
                
        elif part2 == 'ستون':
            if part1 == 'أول':
                return 61
            elif part1 == 'ثاني':
                return 62
            elif part1 == 'ثالث':
                return 63
            elif part1 == 'رابع':
                return 64
            elif part1 == 'خمس':
                return 65
            elif part1 == 'ست':
                return 66
            elif part1 == 'سبع':
                return 67
            elif part1 == 'ثمان':
                return 68
            elif part1 == 'تسع':
                return 69
                
        elif part2 == 'سبعون':
            if part1 == 'أول':
                return 71
            elif part1 == 'ثاني':
                return 72
            elif part1 == 'ثالث':
                return 73
            elif part1 == 'رابع':
                return 74
            elif part1 == 'خمس':
                return 75
            elif part1 == 'ست':
                return 76
            elif part1 == 'سبع':
                return 77
            elif part1 == 'ثمان':
                return 78
            elif part1 == 'تسع':
                return 79
                
        elif part2 == 'ثمانون':
            if part1 == 'أول':
                return 81
            elif part1 == 'ثاني':
                return 82
            elif part1 == 'ثالث':
                return 83
            elif part1 == 'رابع':
                return 84
            elif part1 == 'خمس':
                return 85
            elif part1 == 'ست':
                return 86
            elif part1 == 'سبع':
                return 87
            elif part1 == 'ثمان':
                return 88
            elif part1 == 'تسع':
                return 89
                
        elif part2 == 'تسعون':
            if part1 == 'أول':
                return 91
            elif part1 == 'ثاني':
                return 92
            elif part1 == 'ثالث':
                return 93
            elif part1 == 'رابع':
                return 94
            elif part1 == 'خمس':
                return 95
            elif part1 == 'ست':
                return 96
            elif part1 == 'سبع':
                return 97
            elif part1 == 'ثمان':
                return 98
            elif part1 == 'تسع':
                return 99
        
        return 0
    
    def _parse_single_number(self, text):
        """Parse single number from text."""
        # Handle teens
        if 'حادي عشر' in text:
            return 11
        if 'ثاني عشر' in text:
            return 12
        if 'ثالث عشر' in text:
            return 13
        if 'رابع عشر' in text:
            return 14
        if 'خامس عشر' in text:
            return 15
        if 'سادس عشر' in text:
            return 16
        if 'سابع عشر' in text:
            return 17
        if 'ثامن عشر' in text:
            return 18
        if 'تاسع عشر' in text:
            return 19
        
        # Handle basic numbers
        if 'أول' in text:
            return 1
        if 'ثاني' in text:
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
        
        # Handle tens
        if 'عشرون' in text:
            return 20
        if 'ثلاثون' in text:
            return 30
        if 'أربعون' in text:
            return 40
        if 'خمسون' in text:
            return 50
        if 'ستون' in text:
            return 60
        if 'سبعون' in text:
            return 70
        if 'ثمانون' in text:
            return 80
        if 'تسعون' in text:
            return 90
        
        return 0


def process_json_file(input_file, output_file=None):
    """Process JSON file and convert article names to numbers."""
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of articles")
    
    converter = ArabicArticleConverter()
    processed_data = []
    stats = {
        'total': len(data),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, article in enumerate(data):
        if not isinstance(article, dict) or 'article' not in article:
            stats['errors'].append(f"Article {i+1}: Invalid format")
            continue
            
        article_text = article['article']
        article_number = converter.extract_number(article_text)
        
        if article_number > 0:
            # Create new article entry with numeric format
            new_article = article.copy()
            new_article['article_number'] = article_number
            new_article['article_arabic'] = article_text
            new_article['article'] = f"المادة {article_number}"
            
            processed_data.append(new_article)
            stats['successful'] += 1
        else:
            # Keep original if conversion failed
            processed_data.append(article)
            stats['failed'] += 1
            stats['errors'].append(f"Article {i+1}: '{article_text}' -> Could not convert")
    
    # Write output file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    return processed_data, stats


def main():
    """Main function."""
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
        processed_data, stats = process_json_file(args.input_file, output_file)
        
        # Print statistics
        print(f"\n📊 Conversion Statistics:")
        print(f"Total articles: {stats['total']}")
        print(f"Successful conversions: {stats['successful']}")
        print(f"Failed conversions: {stats['failed']}")
        
        if stats['errors']:
            print(f"\n❌ Conversion Errors (showing first 10):")
            for error in stats['errors'][:10]:
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
        if output_file and not args.stats_only:
            print(f"\n✅ Output written to: {output_file}")
            
        # Show sample of converted articles
        if processed_data:
            print(f"\n📝 Sample of converted articles:")
            for i, article in enumerate(processed_data[:10]):
                if 'article_number' in article:
                    print(f"  {article['article_number']}: {article['article']}")
            if len(processed_data) > 10:
                print(f"  ... and {len(processed_data) - 10} more articles")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Simple script to convert Arabic article sections to numbers.
"""

import json
import re


def extract_article_number(article_text):
    """Extract article number from Arabic article text."""
    
    # Arabic number mappings
    arabic_numbers = {
        'أول': 1, 'ثاني': 2, 'ثالث': 3, 'رابع': 4, 'خامس': 5,
        'سادس': 6, 'سابع': 7, 'ثامن': 8, 'تاسع': 9, 'عاشر': 10,
        'حادي عشر': 11, 'ثاني عشر': 12, 'ثالث عشر': 13, 'رابع عشر': 14,
        'خامس عشر': 15, 'سادس عشر': 16, 'سابع عشر': 17, 'ثامن عشر': 18,
        'تاسع عشر': 19, 'عشرون': 20, 'ثلاثون': 30, 'أربعون': 40,
        'خمسون': 50, 'ستون': 60, 'سبعون': 70, 'ثمانون': 80, 'تسعون': 90
    }
    
    # Remove "المادة" prefix
    text = re.sub(r'^المادة\s*', '', article_text.strip())
    
    # Handle special cases
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
    
    # Handle compound numbers (like خمسة وعشرون = 25)
    if 'و' in text:
        parts = text.split('و')
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            
            # Remove feminine suffixes
            if part1.endswith('ة'):
                part1 = part1[:-1]
            if part2.endswith('ة'):
                part2 = part2[:-1]
                
            # Handle tens
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
            elif part2 == 'ثلاثون':
                if part1 == 'خمس':
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
                if part1 == 'خمس':
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
                if part1 == 'خمس':
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
                if part1 == 'خمس':
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
                if part1 == 'خمس':
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
                if part1 == 'خمس':
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
                if part1 == 'خمس':
                    return 95
                elif part1 == 'ست':
                    return 96
                elif part1 == 'سبع':
                    return 97
                elif part1 == 'ثمان':
                    return 98
                elif part1 == 'تسع':
                    return 99
    
    # Handle teens (11-19)
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
    
    # Handle twenties (20-29)
    if 'عشرون' in text:
        if 'ثاني' in text:
            return 22
        elif 'ثالث' in text:
            return 23
        elif 'رابع' in text:
            return 24
        elif 'خامس' in text:
            return 25
        elif 'سادس' in text:
            return 26
        elif 'سابع' in text:
            return 27
        elif 'ثامن' in text:
            return 28
        elif 'تاسع' in text:
            return 29
        else:
            return 20
    
    # Handle thirties (30-39)
    if 'ثلاثون' in text:
        if 'أول' in text:
            return 31
        elif 'ثاني' in text:
            return 32
        elif 'ثالث' in text:
            return 33
        elif 'رابع' in text:
            return 34
        elif 'خامس' in text:
            return 35
        elif 'سادس' in text:
            return 36
        elif 'سابع' in text:
            return 37
        elif 'ثامن' in text:
            return 38
        elif 'تاسع' in text:
            return 39
        else:
            return 30
    
    # Handle forties (40-49)
    if 'أربعون' in text:
        if 'أول' in text:
            return 41
        elif 'ثاني' in text:
            return 42
        elif 'ثالث' in text:
            return 43
        elif 'رابع' in text:
            return 44
        elif 'خامس' in text:
            return 45
        elif 'سادس' in text:
            return 46
        elif 'سابع' in text:
            return 47
        elif 'ثامن' in text:
            return 48
        elif 'تاسع' in text:
            return 49
        else:
            return 40
    
    # Handle fifties (50-59)
    if 'خمسون' in text:
        if 'أول' in text:
            return 51
        elif 'ثاني' in text:
            return 52
        elif 'ثالث' in text:
            return 53
        elif 'رابع' in text:
            return 54
        elif 'خامس' in text:
            return 55
        elif 'سادس' in text:
            return 56
        elif 'سابع' in text:
            return 57
        elif 'ثامن' in text:
            return 58
        elif 'تاسع' in text:
            return 59
        else:
            return 50
    
    # Handle sixties (60-69)
    if 'ستون' in text:
        if 'أول' in text:
            return 61
        elif 'ثاني' in text:
            return 62
        elif 'ثالث' in text:
            return 63
        elif 'رابع' in text:
            return 64
        elif 'خامس' in text:
            return 65
        elif 'سادس' in text:
            return 66
        elif 'سابع' in text:
            return 67
        elif 'ثامن' in text:
            return 68
        elif 'تاسع' in text:
            return 69
        else:
            return 60
    
    # Handle seventies (70-79)
    if 'سبعون' in text:
        if 'أول' in text:
            return 71
        elif 'ثاني' in text:
            return 72
        elif 'ثالث' in text:
            return 73
        elif 'رابع' in text:
            return 74
        elif 'خامس' in text:
            return 75
        elif 'سادس' in text:
            return 76
        elif 'سابع' in text:
            return 77
        elif 'ثامن' in text:
            return 78
        elif 'تاسع' in text:
            return 79
        else:
            return 70
    
    # Handle eighties (80-89)
    if 'ثمانون' in text:
        if 'أول' in text:
            return 81
        elif 'ثاني' in text:
            return 82
        elif 'ثالث' in text:
            return 83
        elif 'رابع' in text:
            return 84
        elif 'خامس' in text:
            return 85
        elif 'سادس' in text:
            return 86
        elif 'سابع' in text:
            return 87
        elif 'ثامن' in text:
            return 88
        elif 'تاسع' in text:
            return 89
        else:
            return 80
    
    # Handle nineties (90-99)
    if 'تسعون' in text:
        if 'أول' in text:
            return 91
        elif 'ثاني' in text:
            return 92
        elif 'ثالث' in text:
            return 93
        elif 'رابع' in text:
            return 94
        elif 'خامس' in text:
            return 95
        elif 'سادس' in text:
            return 96
        elif 'سابع' in text:
            return 97
        elif 'ثامن' in text:
            return 98
        elif 'تاسع' in text:
            return 99
        else:
            return 90
    
    return 0


def test_converter():
    """Test the converter with sample data."""
    test_cases = [
        "المادة الأولى",
        "المادة الثانية", 
        "المادة الثالثة",
        "المادة الخامسة والعشرون",
        "المادة الحادية والثلاثون",
        "المادة الثانية والثلاثون",
        "المادة الخامسة والثلاثون",
        "المادة السابعة والثلاثون"
    ]
    
    print("Testing Arabic Article Number Converter:")
    print("=" * 50)
    
    for test_case in test_cases:
        number = extract_article_number(test_case)
        print(f"{test_case} -> {number}")
    
    print("\nTesting with actual JSON file...")
    
    # Read and process the JSON file
    try:
        with open('data_set/files/saudi_labor_law.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\nProcessing {len(data)} articles...")
        
        successful = 0
        failed = 0
        
        for i, article in enumerate(data[:20]):  # Test first 20 articles
            if 'article' in article:
                article_text = article['article']
                number = extract_article_number(article_text)
                
                if number > 0:
                    print(f"Article {i+1}: {article_text} -> {number}")
                    successful += 1
                else:
                    print(f"Article {i+1}: {article_text} -> FAILED")
                    failed += 1
        
        print(f"\nResults: {successful} successful, {failed} failed")
        
    except Exception as e:
        print(f"Error reading JSON file: {e}")


if __name__ == "__main__":
    test_converter()

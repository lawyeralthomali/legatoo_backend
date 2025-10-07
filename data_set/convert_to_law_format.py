#!/usr/bin/env python3
"""
Convert Extracted Legal Structure to Correct Law Format

This script converts the extracted_legal_structure.json to the correct
law JSON format for database upload.
"""

import json
import os
from datetime import datetime

def convert_to_law_format(input_file: str, output_file: str):
    """Convert extracted structure to correct law format."""
    
    print(f"🔄 Converting {input_file} to correct law format...")
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract law source data
        if "law_sources" not in data or not data["law_sources"]:
            print("❌ No law_sources found in input file")
            return False
        
        law_source = data["law_sources"][0]
        
        # Create the correct structure
        converted_data = {
            "law_sources": [
                {
                    "name": law_source.get("name", "Unknown Law"),
                    "type": law_source.get("type", "law"),
                    "jurisdiction": law_source.get("jurisdiction"),
                    "issuing_authority": law_source.get("issuing_authority"),
                    "issue_date": convert_date_format(law_source.get("issue_date")),
                    "last_update": convert_date_format(law_source.get("last_update")),
                    "description": law_source.get("description"),
                    "source_url": law_source.get("source_url"),
                    "branches": []
                }
            ],
            "processing_report": data.get("processing_report", {})
        }
        
        # Process branches
        branches = law_source.get("branches", [])
        for branch in branches:
            converted_branch = {
                "branch_number": branch.get("branch_number", ""),
                "branch_name": branch.get("branch_name", ""),
                "description": branch.get("description"),
                "order_index": branch.get("order_index", 0),
                "chapters": []
            }
            
            # Process chapters
            chapters = branch.get("chapters", [])
            for chapter in chapters:
                converted_chapter = {
                    "chapter_number": chapter.get("chapter_number", ""),
                    "chapter_name": chapter.get("chapter_name", ""),
                    "description": chapter.get("description"),
                    "order_index": chapter.get("order_index", 0),
                    "articles": []
                }
                
                # Process articles
                articles = chapter.get("articles", [])
                for article in articles:
                    converted_article = {
                        "article_number": article.get("article_number", ""),
                        "title": article.get("title"),
                        "content": article.get("content", ""),
                        "keywords": article.get("keywords", []),
                        "order_index": article.get("order_index", 0)
                    }
                    converted_chapter["articles"].append(converted_article)
                
                converted_branch["chapters"].append(converted_chapter)
            
            converted_data["law_sources"][0]["branches"].append(converted_branch)
        
        # Write the converted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        total_branches = len(converted_data["law_sources"][0]["branches"])
        total_chapters = sum(len(branch["chapters"]) for branch in converted_data["law_sources"][0]["branches"])
        total_articles = sum(len(chapter["articles"]) for branch in converted_data["law_sources"][0]["branches"] for chapter in branch["chapters"])
        
        print("✅ Conversion completed successfully!")
        print(f"📊 Statistics:")
        print(f"   - Branches: {total_branches}")
        print(f"   - Chapters: {total_chapters}")
        print(f"   - Articles: {total_articles}")
        print(f"📁 Output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        return False

def convert_date_format(date_str):
    """Convert date format to YYYY-MM-DD if needed."""
    if not date_str:
        return None
    
    # If already in correct format, return as is
    if len(date_str) == 10 and date_str.count('-') == 2:
        return date_str
    
    # Try to parse and convert common formats
    try:
        # Handle Hijri dates like "1426/08/23هـ"
        if 'هـ' in date_str:
            date_str = date_str.replace('هـ', '').strip()
        
        # Handle different separators
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year, month, day = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    except:
        return date_str

def main():
    """Main function."""
    print("=" * 60)
    print("🔄 LAW JSON FORMAT CONVERTER")
    print("=" * 60)
    
    # Input and output files
    input_file = "files/extracted_legal_structure.json"
    output_file = "files/converted_law_structure.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Convert the file
    success = convert_to_law_format(input_file, output_file)
    
    if success:
        print(f"\n🎉 Conversion completed!")
        print(f"📁 You can now upload: {output_file}")
        print(f"🚀 Run: python test_json_upload.py")
    else:
        print(f"\n❌ Conversion failed!")

if __name__ == "__main__":
    main()

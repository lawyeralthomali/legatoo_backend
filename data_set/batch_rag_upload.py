"""
Batch RAG Upload Script

This script uploads all law JSON files from the data_set/files directory
to the RAG system using the /api/v1/rag/upload endpoint.

Features:
- Flattens hierarchical structure (branches → chapters → articles) 
- Handles nested JSON format
- Validates data before upload
- Provides detailed progress logging
- Generates upload summary report
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RAGUploadClient:
    """Client for uploading laws to RAG system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize RAG upload client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.upload_endpoint = f"{base_url}/api/v1/rag/upload"
        self.status_endpoint = f"{base_url}/api/v1/rag/status"
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_articles': 0,
            'total_chunks': 0,
            'total_processing_time': 0.0,
            'errors': []
        }
    
    def flatten_law_structure(self, law_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten hierarchical law structure to simple format for RAG.
        
        Extracts all articles from branches → chapters → articles structure
        and creates a flat list of articles.
        
        Args:
            law_data: Law data with nested structure
            
        Returns:
            Flattened law data ready for RAG upload
        """
        # Extract law source metadata
        law_source = law_data.get('law_sources', [{}])[0]
        
        # Collect all articles from all branches and chapters
        articles = []
        
        for branch in law_source.get('branches', []):
            branch_number = branch.get('branch_number', '')
            branch_name = branch.get('branch_name', '')
            
            for chapter in branch.get('chapters', []):
                chapter_number = chapter.get('chapter_number', '')
                chapter_name = chapter.get('chapter_name', '')
                
                for article in chapter.get('articles', []):
                    # Create enriched article with context
                    enriched_article = {
                        'article_number': article.get('article_number', ''),
                        'title': article.get('title', ''),
                        'content': article.get('content', ''),
                        'keywords': article.get('keywords', [])
                    }
                    
                    # Add hierarchical context to keywords
                    context_keywords = []
                    if branch_name:
                        context_keywords.append(f"الباب: {branch_name}")
                    if chapter_name:
                        context_keywords.append(f"الفصل: {chapter_name}")
                    
                    enriched_article['keywords'].extend(context_keywords)
                    articles.append(enriched_article)
        
        # Parse date (handle both formats)
        issue_date = law_source.get('issue_date', '')
        if issue_date:
            # Try to convert Hijri date to simple format
            # For now, keep as-is since backend can handle various formats
            pass
        
        # Create flattened structure
        flattened = {
            'law_name': law_source.get('name', 'Unknown Law'),
            'law_type': law_source.get('type', 'law'),
            'jurisdiction': law_source.get('jurisdiction', 'المملكة العربية السعودية'),
            'issuing_authority': law_source.get('issuing_authority'),
            'issue_date': issue_date if issue_date else None,
            'description': law_source.get('description'),
            'source_url': law_source.get('source_url'),
            'articles': articles
        }
        
        return flattened
    
    def upload_law(self, law_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Upload a single law to RAG system.
        
        Args:
            law_data: Law data in RAG-compatible format
            filename: Source filename for logging
            
        Returns:
            Upload result
        """
        try:
            print(f"\n📤 Uploading: {law_data['law_name']}")
            print(f"   Source: {filename}")
            print(f"   Articles: {len(law_data['articles'])}")
            
            # Make API request
            response = requests.post(
                self.upload_endpoint,
                json=law_data,
                headers={'Content-Type': 'application/json'},
                timeout=300  # 5 minutes timeout for large files
            )
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    data = result.get('data', {})
                    print(f"   ✅ Success!")
                    print(f"   Law Source ID: {data.get('law_source_id')}")
                    print(f"   Articles Created: {data.get('articles_created')}")
                    print(f"   Chunks Created: {data.get('chunks_created')}")
                    print(f"   Processing Time: {data.get('processing_time')}s")
                    
                    # Update statistics
                    self.stats['successful_uploads'] += 1
                    self.stats['total_articles'] += data.get('articles_created', 0)
                    self.stats['total_chunks'] += data.get('chunks_created', 0)
                    self.stats['total_processing_time'] += data.get('processing_time', 0)
                    
                    return {
                        'success': True,
                        'filename': filename,
                        'law_name': law_data['law_name'],
                        'data': data
                    }
                else:
                    error_msg = result.get('message', 'Upload failed')
                    errors = result.get('errors', [])
                    print(f"   ❌ Failed: {error_msg}")
                    for error in errors:
                        print(f"      - {error.get('message')}")
                    
                    self.stats['failed_uploads'] += 1
                    self.stats['errors'].append({
                        'filename': filename,
                        'law_name': law_data['law_name'],
                        'error': error_msg,
                        'details': errors
                    })
                    
                    return {
                        'success': False,
                        'filename': filename,
                        'law_name': law_data['law_name'],
                        'error': error_msg
                    }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   {response.text[:200]}")
                
                self.stats['failed_uploads'] += 1
                self.stats['errors'].append({
                    'filename': filename,
                    'law_name': law_data['law_name'],
                    'error': error_msg
                })
                
                return {
                    'success': False,
                    'filename': filename,
                    'law_name': law_data['law_name'],
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout (>5 minutes)"
            print(f"   ❌ Timeout: {error_msg}")
            self.stats['failed_uploads'] += 1
            self.stats['errors'].append({
                'filename': filename,
                'law_name': law_data.get('law_name', 'Unknown'),
                'error': error_msg
            })
            return {'success': False, 'filename': filename, 'error': error_msg}
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Exception: {error_msg}")
            self.stats['failed_uploads'] += 1
            self.stats['errors'].append({
                'filename': filename,
                'law_name': law_data.get('law_name', 'Unknown'),
                'error': error_msg
            })
            return {'success': False, 'filename': filename, 'error': error_msg}
    
    def check_server_status(self) -> bool:
        """
        Check if RAG server is running and operational.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            print("🔍 Checking RAG server status...")
            response = requests.get(self.status_endpoint, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    print(f"✅ RAG Server Status: {data.get('status')}")
                    print(f"   Law Sources: {data.get('total_law_sources')}")
                    print(f"   Articles: {data.get('total_articles')}")
                    print(f"   Chunks: {data.get('total_chunks')}")
                    print(f"   Embedding Coverage: {data.get('embedding_coverage')}%")
                    return True
            
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Cannot connect to server: {str(e)}")
            print(f"   Make sure the server is running at {self.base_url}")
            return False
    
    def process_directory(self, directory: str) -> None:
        """
        Process all JSON files in a directory.
        
        Args:
            directory: Path to directory containing JSON files
        """
        # Check server first
        if not self.check_server_status():
            print("\n❌ Server is not accessible. Please start the server first.")
            return
        
        print(f"\n📁 Scanning directory: {directory}")
        
        # Get all JSON files
        json_files = sorted(Path(directory).glob('*.json'))
        self.stats['total_files'] = len(json_files)
        
        if not json_files:
            print("❌ No JSON files found in directory")
            return
        
        print(f"📊 Found {len(json_files)} JSON files\n")
        
        # Process each file
        results = []
        for idx, json_file in enumerate(json_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing {idx}/{len(json_files)}: {json_file.name}")
            print(f"{'='*60}")
            
            try:
                # Read JSON file
                with open(json_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # Flatten structure
                flattened_data = self.flatten_law_structure(raw_data)
                
                # Upload to RAG
                result = self.upload_law(flattened_data, json_file.name)
                results.append(result)
                
                # Small delay between uploads to avoid overwhelming server
                time.sleep(1)
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Parse Error: {str(e)}")
                self.stats['failed_uploads'] += 1
                self.stats['errors'].append({
                    'filename': json_file.name,
                    'error': f"JSON Parse Error: {str(e)}"
                })
                
            except Exception as e:
                print(f"   ❌ Unexpected Error: {str(e)}")
                self.stats['failed_uploads'] += 1
                self.stats['errors'].append({
                    'filename': json_file.name,
                    'error': f"Unexpected Error: {str(e)}"
                })
        
        # Generate summary
        self.print_summary(results)
        self.save_summary_report(results)
    
    def print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print upload summary."""
        print("\n" + "="*60)
        print("📊 UPLOAD SUMMARY")
        print("="*60)
        print(f"Total Files Processed: {self.stats['total_files']}")
        print(f"✅ Successful Uploads: {self.stats['successful_uploads']}")
        print(f"❌ Failed Uploads: {self.stats['failed_uploads']}")
        print(f"📄 Total Articles Created: {self.stats['total_articles']}")
        print(f"🔖 Total Chunks Created: {self.stats['total_chunks']}")
        print(f"⏱️  Total Processing Time: {self.stats['total_processing_time']:.2f}s")
        
        if self.stats['errors']:
            print(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"   - {error['filename']}: {error['error']}")
        
        print("="*60)
    
    def save_summary_report(self, results: List[Dict[str, Any]]) -> None:
        """Save detailed summary report to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"data_set/rag_upload_summary_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'results': results
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📝 Summary report saved to: {report_path}")
        except Exception as e:
            print(f"\n⚠️ Failed to save report: {str(e)}")


def main():
    """Main function."""
    print("="*60)
    print("🚀 RAG BATCH UPLOAD SCRIPT")
    print("="*60)
    print("This script uploads law JSON files to the RAG system")
    print("="*60)
    
    # Configuration
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
    FILES_DIR = 'data_set/files'
    
    # Check if directory exists
    if not os.path.exists(FILES_DIR):
        print(f"❌ Directory not found: {FILES_DIR}")
        print(f"   Current directory: {os.getcwd()}")
        return
    
    # Initialize client
    client = RAGUploadClient(base_url=BASE_URL)
    
    # Process all files
    start_time = time.time()
    client.process_directory(FILES_DIR)
    total_time = time.time() - start_time
    
    print(f"\n⏱️  Total Execution Time: {total_time:.2f}s")
    print("✅ Batch upload completed!")


if __name__ == "__main__":
    main()


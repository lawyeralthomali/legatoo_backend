#!/usr/bin/env python3
"""
Batch Laws Upload Script
رفع دفعات من الأنظمة والقوانين

This script reads all JSON files from the data_set/files/ folder and uploads them
to the database using the legal laws API endpoint.

Usage:
    python batch_upload_laws.py

Requirements:
    - All JSON files must be in the data_set/files/ folder
    - JSON files must follow the expected law structure format
    - Server must be running on http://127.0.0.1:8000
    - Valid authentication token required
"""

import os
import sys
import json
import requests
import logging
from typing import List, Dict, Any
from pathlib import Path
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_laws_upload.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BatchLawsUploader:
    """Handles batch uploading of JSON legal law files."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.upload_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_laws': 0,
            'total_articles': 0,
            'errors': []
        }
        
    def authenticate(self) -> bool:
        """Authenticate with the API."""
        try:
            login_data = {
                "email": "legatoo@althomalilawfirm.sa",
                "password": "Zaq1zaq1"
            }
            
            logger.info("🔐 Authenticating...")
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.auth_token = data['data']['access_token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    logger.info("✅ Authentication successful")
                    return True
            
            logger.error(f"❌ Authentication failed: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def clean_json_comments(self, json_str: str) -> str:
        """Remove JavaScript-style comments from JSON string."""
        # Remove single-line comments (// ...)
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        # Remove multi-line comments (/* ... */)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean comments
            content = self.clean_json_comments(content)
            
            # Parse JSON with strict=False to allow control characters
            data = json.loads(content, strict=False)
            logger.info(f"✅ Successfully read: {file_path.name}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in {file_path.name}: {str(e)}")
            logger.error(f"   Line {e.lineno}, Column {e.colno}")
            self.upload_stats['errors'].append({
                'file': str(file_path),
                'error': f'JSON decode error: {str(e)}'
            })
            return None
            
        except Exception as e:
            logger.error(f"❌ Error reading {file_path.name}: {str(e)}")
            self.upload_stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            return None
    
    def validate_law_data(self, data: Dict[str, Any], file_name: str) -> bool:
        """Validate law data structure."""
        if not isinstance(data, dict):
            logger.error(f"❌ {file_name}: Data must be a dictionary")
            return False
        
        if 'law_sources' not in data:
            logger.error(f"❌ {file_name}: Missing 'law_sources' field")
            return False
        
        if not isinstance(data['law_sources'], list):
            logger.error(f"❌ {file_name}: 'law_sources' must be a list")
            return False
        
        # Validate each law source
        for i, law in enumerate(data['law_sources'], 1):
            required_fields = ['name', 'type']
            
            for field in required_fields:
                if field not in law:
                    logger.warning(f"⚠️  {file_name} - Law {i}: Missing '{field}' field")
            
            # Check for articles or branches
            has_structure = any(key in law for key in ['branches', 'chapters', 'articles'])
            if not has_structure:
                logger.warning(f"⚠️  {file_name} - Law {i}: No structure found (branches/chapters/articles)")
        
        logger.info(f"✅ {file_name}: Validation passed ({len(data['law_sources'])} laws)")
        return True
    
    def upload_law(self, data: Dict[str, Any], file_path: Path) -> bool:
        """Upload law data to the API."""
        try:
            laws_count = len(data.get('law_sources', []))
            logger.info(f"📤 Uploading {laws_count} laws from {file_path.name}...")
            
            # Use the upload-json endpoint
            endpoint = f"{self.base_url}/api/v1/laws/upload-json"
            
            # Send as file upload (multipart/form-data)
            with open(file_path, 'rb') as f:
                files = {'json_file': (file_path.name, f, 'application/json')}
                response = self.session.post(endpoint, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"✅ Successfully uploaded {file_path.name}")
                    logger.info(f"   Laws processed: {laws_count}")
                    
                    # Extract stats from response
                    if 'data' in result and isinstance(result['data'], dict):
                        total_articles = result['data'].get('total_articles', 0)
                        if total_articles > 0:
                            logger.info(f"   Articles created: {total_articles}")
                            self.upload_stats['total_articles'] += total_articles
                    
                    self.upload_stats['total_laws'] += laws_count
                    return True
                else:
                    logger.error(f"❌ Upload failed for {file_path.name}: {result.get('message')}")
                    self.upload_stats['errors'].append({
                        'file': file_path.name,
                        'error': result.get('message'),
                        'details': result.get('errors', [])
                    })
                    return False
            else:
                logger.error(f"❌ HTTP {response.status_code} for {file_path.name}")
                logger.error(f"   Response: {response.text[:500]}")
                self.upload_stats['errors'].append({
                    'file': file_path.name,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text[:500]
                })
                return False
                
        except Exception as e:
            logger.error(f"❌ Upload error for {file_path.name}: {str(e)}")
            self.upload_stats['errors'].append({
                'file': file_path.name,
                'error': str(e)
            })
            return False
    
    def find_law_files(self, directory: str = "files") -> List[Path]:
        """Find all JSON files in the laws directory."""
        # Get script directory
        script_dir = Path(__file__).parent
        laws_dir = script_dir / directory
        
        if not laws_dir.exists():
            logger.error(f"❌ Laws directory not found: {laws_dir}")
            return []
        
        # Find all JSON files
        json_files = []
        for file_path in laws_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.json':
                json_files.append(file_path)
        
        json_files.sort()
        logger.info(f"📁 Found {len(json_files)} JSON files in {laws_dir}")
        
        return json_files
    
    def run(self, directory: str = "files") -> None:
        """Main execution method."""
        logger.info("="*80)
        logger.info("🚀 Starting Batch Laws Upload")
        logger.info("="*80)
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Cannot proceed without authentication")
            return
        
        # Find files
        json_files = self.find_law_files(directory)
        
        if not json_files:
            logger.warning("⚠️  No JSON files found to upload")
            return
        
        self.upload_stats['total_files'] = len(json_files)
        
        # Process each file
        for i, file_path in enumerate(json_files, 1):
            logger.info("")
            logger.info(f"📄 Processing file {i}/{len(json_files)}: {file_path.name}")
            logger.info("-"*80)
            
            # Read JSON
            data = self.read_json_file(file_path)
            if data is None:
                self.upload_stats['failed'] += 1
                continue
            
            # Validate
            if not self.validate_law_data(data, file_path.name):
                self.upload_stats['failed'] += 1
                continue
            
            # Upload
            if self.upload_law(data, file_path):
                self.upload_stats['successful'] += 1
            else:
                self.upload_stats['failed'] += 1
            
            # Small delay between uploads to avoid overwhelming the server
            time.sleep(0.5)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print upload statistics summary."""
        logger.info("")
        logger.info("="*80)
        logger.info("📊 UPLOAD SUMMARY")
        logger.info("="*80)
        logger.info(f"📁 Total files processed: {self.upload_stats['total_files']}")
        logger.info(f"✅ Successful uploads: {self.upload_stats['successful']}")
        logger.info(f"❌ Failed uploads: {self.upload_stats['failed']}")
        logger.info(f"⚖️  Total laws uploaded: {self.upload_stats['total_laws']}")
        logger.info(f"📜 Total articles created: {self.upload_stats['total_articles']}")
        logger.info("="*80)
        
        if self.upload_stats['errors']:
            logger.info("")
            logger.info("❌ ERRORS:")
            for error in self.upload_stats['errors']:
                logger.error(f"   File: {error['file']}")
                logger.error(f"   Error: {error['error']}")
                if 'details' in error:
                    logger.error(f"   Details: {error['details']}")
                logger.error("")
        
        # Write summary to file
        summary_path = Path(__file__).parent / 'batch_laws_upload_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(self.upload_stats, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 Summary saved to: {summary_path}")


def main():
    """Main entry point."""
    try:
        uploader = BatchLawsUploader()
        uploader.run(directory="files")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Upload interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


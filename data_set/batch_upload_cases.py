#!/usr/bin/env python3
"""
Batch Cases Upload Script
رفع دفعات من القضايا القانونية

This script reads all JSON files from the data_set/cases/ folder and uploads them
to the database using the legal cases API endpoint.

Usage:
    python batch_upload_cases.py

Requirements:
    - All JSON files must be in the data_set/cases/ folder
    - JSON files must follow the expected case structure format
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_cases_upload.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BatchCasesUploader:
    """Handles batch uploading of JSON legal case files."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.upload_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_cases': 0,
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
        """
        Remove JavaScript-style comments from JSON string.
        
        Args:
            json_str: JSON string potentially containing comments
            
        Returns:
            Cleaned JSON string
        """
        # Remove single-line comments (// ...)
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        # Remove multi-line comments (/* ... */)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Read and parse JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean comments
            content = self.clean_json_comments(content)
            
            # Parse JSON
            data = json.loads(content)
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
    
    def validate_case_data(self, data: Dict[str, Any], file_name: str) -> bool:
        """
        Validate case data structure.
        
        Args:
            data: Parsed JSON data
            file_name: Name of the file being validated
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.error(f"❌ {file_name}: Data must be a dictionary")
            return False
        
        if 'legal_cases' not in data:
            logger.error(f"❌ {file_name}: Missing 'legal_cases' field")
            return False
        
        if not isinstance(data['legal_cases'], list):
            logger.error(f"❌ {file_name}: 'legal_cases' must be a list")
            return False
        
        # Validate each case
        for i, case in enumerate(data['legal_cases'], 1):
            required_fields = ['case_number', 'title', 'description', 'sections']
            
            for field in required_fields:
                if field not in case:
                    logger.warning(f"⚠️ {file_name} - Case {i}: Missing '{field}' field")
            
            # Validate sections
            if 'sections' in case and isinstance(case['sections'], list):
                for j, section in enumerate(case['sections'], 1):
                    if 'section_type' not in section or 'content' not in section:
                        logger.warning(f"⚠️ {file_name} - Case {i}, Section {j}: Missing required fields")
        
        logger.info(f"✅ {file_name}: Validation passed ({len(data['legal_cases'])} cases)")
        return True
    
    def upload_cases(self, data: Dict[str, Any], file_path: Path) -> bool:
        """
        Upload cases data to the API.
        
        Args:
            data: Case data to upload
            file_path: Path to the source file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cases_count = len(data.get('legal_cases', []))
            logger.info(f"📤 Uploading {cases_count} cases from {file_path.name}...")
            
            # Use the upload-json endpoint (expects file upload)
            endpoint = f"{self.base_url}/api/v1/legal-cases/upload-json"
            
            # Upload as multipart/form-data file
            with open(file_path, 'rb') as f:
                files = {'json_file': (file_path.name, f, 'application/json')}
                response = self.session.post(endpoint, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"✅ Successfully uploaded {file_path.name}")
                    logger.info(f"   Cases processed: {cases_count}")
                    self.upload_stats['total_cases'] += cases_count
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
    
    def find_case_files(self, directory: str = "cases") -> List[Path]:
        """
        Find all JSON files in the cases directory.
        
        Args:
            directory: Directory name to search (relative to data_set/)
            
        Returns:
            List of Path objects for found JSON files
        """
        # Get script directory
        script_dir = Path(__file__).parent
        cases_dir = script_dir / directory
        
        if not cases_dir.exists():
            logger.error(f"❌ Cases directory not found: {cases_dir}")
            return []
        
        # Find all JSON files (including .json files with comma in name like "1,json")
        json_files = []
        for file_path in cases_dir.iterdir():
            if file_path.is_file() and ('json' in file_path.name.lower()):
                json_files.append(file_path)
        
        json_files.sort()
        logger.info(f"📁 Found {len(json_files)} JSON files in {cases_dir}")
        
        return json_files
    
    def run(self, directory: str = "cases") -> None:
        """
        Main execution method.
        
        Args:
            directory: Directory containing case JSON files
        """
        logger.info("="*60)
        logger.info("🚀 Starting Batch Cases Upload")
        logger.info("="*60)
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Cannot proceed without authentication")
            return
        
        # Find files
        json_files = self.find_case_files(directory)
        
        if not json_files:
            logger.warning("⚠️ No JSON files found to upload")
            return
        
        self.upload_stats['total_files'] = len(json_files)
        
        # Process each file
        for i, file_path in enumerate(json_files, 1):
            logger.info("")
            logger.info(f"📄 Processing file {i}/{len(json_files)}: {file_path.name}")
            logger.info("-"*60)
            
            # Read JSON
            data = self.read_json_file(file_path)
            if data is None:
                self.upload_stats['failed'] += 1
                continue
            
            # Validate
            if not self.validate_case_data(data, file_path.name):
                self.upload_stats['failed'] += 1
                continue
            
            # Upload
            if self.upload_cases(data, file_path):
                self.upload_stats['successful'] += 1
            else:
                self.upload_stats['failed'] += 1
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print upload statistics summary."""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 UPLOAD SUMMARY")
        logger.info("="*60)
        logger.info(f"📁 Total files processed: {self.upload_stats['total_files']}")
        logger.info(f"✅ Successful uploads: {self.upload_stats['successful']}")
        logger.info(f"❌ Failed uploads: {self.upload_stats['failed']}")
        logger.info(f"⚖️ Total cases uploaded: {self.upload_stats['total_cases']}")
        logger.info("="*60)
        
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
        summary_path = Path(__file__).parent / 'batch_cases_upload_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(self.upload_stats, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 Summary saved to: {summary_path}")


def main():
    """Main entry point."""
    try:
        uploader = BatchCasesUploader()
        uploader.run(directory="cases")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Upload interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

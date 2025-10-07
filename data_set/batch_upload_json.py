#!/usr/bin/env python3
"""
Batch JSON Upload Script

This script reads all JSON files from the data_set folder and uploads them
to the database using the legal laws API endpoint.

Usage:
    python batch_upload_json.py

Requirements:
    - All JSON files must be in the data_set/ folder
    - JSON files must follow the expected law structure format
    - Server must be running on http://127.0.0.1:8000
    - Valid authentication token required
"""

import os
import json
import requests
import logging
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchJSONUploader:
    """Handles batch uploading of JSON law files."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with hardcoded credentials."""
        try:
            login_data = {
                "email": "legatoo@althomalilawfirm.sa",
                "password": "Zaq1zaq1"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.auth_token = data["data"]["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {data.get('message')}")
                    return False
            else:
                logger.error(f"❌ Authentication failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def upload_json_file(self, file_path: str) -> Dict[str, Any]:
        """Upload a single JSON file."""
        try:
            logger.info(f"📤 Uploading: {file_path}")
            
            with open(file_path, 'rb') as f:
                files = {
                    'json_file': (os.path.basename(file_path), f, 'application/json')
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/laws/upload-json",
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stats = data["data"]["statistics"]
                    logger.info(f"✅ Success: {stats['total_branches']} branches, {stats['total_chapters']} chapters, {stats['total_articles']} articles")
                    return {"success": True, "data": data["data"]}
                else:
                    logger.error(f"❌ Upload failed: {data.get('message')}")
                    return {"success": False, "error": data.get("message")}
            else:
                logger.error(f"❌ Upload failed: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Upload error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def validate_json_file(self, file_path: str) -> bool:
        """Validate JSON file structure for law data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required structure for law data
            if "law_sources" not in data:
                logger.error(f"❌ Invalid JSON structure in {file_path}: Missing 'law_sources'")
                return False
            
            if not data["law_sources"]:
                logger.error(f"❌ Invalid JSON structure in {file_path}: Empty 'law_sources' array")
                return False
            
            law_source = data["law_sources"][0]
            
            # Validate law source required fields
            required_fields = ["name", "type"]
            for field in required_fields:
                if field not in law_source:
                    logger.error(f"❌ Invalid JSON structure in {file_path}: Missing '{field}' in law_source")
                    return False
            
            # Validate law type
            valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
            if law_source["type"] not in valid_types:
                logger.error(f"❌ Invalid law type in {file_path}: Must be one of {valid_types}")
                return False
            
            # Check for valid structure - either branches->chapters->articles OR direct articles
            has_valid_structure = False
            
            # Check if it has branches structure
            if "branches" in law_source and law_source["branches"]:
                branches = law_source["branches"]
                if isinstance(branches, list):
                    # Check at least one branch has chapters and articles
                    for branch in branches:
                        if "chapters" in branch and branch["chapters"]:
                            for chapter in branch["chapters"]:
                                if "articles" in chapter and chapter["articles"]:
                                    has_valid_structure = True
                                    break
                        if has_valid_structure:
                            break
            
            # Check if it has direct articles structure (like 1.json)
            elif "articles" in law_source and law_source["articles"]:
                articles = law_source["articles"]
                if isinstance(articles, list) and len(articles) > 0:
                    has_valid_structure = True
            
            if not has_valid_structure:
                logger.error(f"❌ Invalid JSON structure in {file_path}: No valid structure found. Must have either branches->chapters->articles OR direct articles")
                return False
            
            logger.info(f"✅ Law JSON structure valid: {file_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format in {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error validating {file_path}: {str(e)}")
            return False
    
    def get_json_files(self, data_set_folder: str = "files") -> List[str]:
        """Get all JSON files from the files folder."""
        data_set_path = Path(data_set_folder)
        
        if not data_set_path.exists():
            logger.error(f"❌ Data set folder not found: {data_set_folder}")
            return []
        
        json_files = list(data_set_path.glob("*.json"))
        
        if not json_files:
            logger.warning(f"⚠️ No JSON files found in {data_set_folder}")
            return []
        
        logger.info(f"📁 Found {len(json_files)} JSON files in {data_set_folder}")
        return [str(f) for f in json_files]
    
    def batch_upload(self, data_set_folder: str = "files") -> Dict[str, Any]:
        """Upload all JSON files from the files folder."""
        logger.info("🚀 Starting batch JSON upload process")
        
        # Get all JSON files
        json_files = self.get_json_files(data_set_folder)
        if not json_files:
            return {"success": False, "message": "No JSON files found"}
        
        # Validate all files first
        valid_files = []
        for file_path in json_files:
            if self.validate_json_file(file_path):
                valid_files.append(file_path)
        
        if not valid_files:
            return {"success": False, "message": "No valid JSON files found"}
        
        logger.info(f"📋 Processing {len(valid_files)} valid JSON files")
        
        # Upload each file
        results = {
            "successful": [],
            "failed": [],
            "total_files": len(valid_files),
            "total_branches": 0,
            "total_chapters": 0,
            "total_articles": 0
        }
        
        for file_path in valid_files:
            result = self.upload_json_file(file_path)
            
            if result["success"]:
                results["successful"].append({
                    "file": file_path,
                    "data": result["data"]
                })
                
                # Accumulate statistics
                stats = result["data"]["statistics"]
                results["total_branches"] += stats["total_branches"]
                results["total_chapters"] += stats["total_chapters"]
                results["total_articles"] += stats["total_articles"]
            else:
                results["failed"].append({
                    "file": file_path,
                    "error": result["error"]
                })
        
        # Summary
        success_count = len(results["successful"])
        fail_count = len(results["failed"])
        
        logger.info("=" * 60)
        logger.info("📊 BATCH UPLOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful uploads: {success_count}")
        logger.info(f"❌ Failed uploads: {fail_count}")
        logger.info(f"📈 Total branches: {results['total_branches']}")
        logger.info(f"📈 Total chapters: {results['total_chapters']}")
        logger.info(f"📈 Total articles: {results['total_articles']}")
        
        if results["failed"]:
            logger.info("\n❌ Failed files:")
            for failed in results["failed"]:
                logger.info(f"   - {failed['file']}: {failed['error']}")
        
        return results


def main():
    """Main function to run the batch upload."""
    print("=" * 60)
    print("🚀 BATCH JSON UPLOAD SCRIPT")
    print("=" * 60)
    
    # Initialize uploader
    uploader = BatchJSONUploader()
    
    # Authenticate with hardcoded credentials
    if not uploader.authenticate():
        print("❌ Authentication failed. Please check your credentials.")
        return
    
    # Run batch upload
    results = uploader.batch_upload()
    
    if results.get("successful"):
        print(f"\n🎉 Batch upload completed successfully!")
        print(f"✅ {len(results['successful'])} files uploaded")
        print(f"📈 Total: {results['total_branches']} branches, {results['total_chapters']} chapters, {results['total_articles']} articles")
    else:
        print(f"\n❌ Batch upload failed")
        if results.get("failed"):
            print(f"❌ {len(results['failed'])} files failed")
        else:
            print(f"❌ {results.get('message', 'Unknown error')}")


if __name__ == "__main__":
    main()

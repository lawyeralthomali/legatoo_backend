"""
Test Script for Similar Laws Endpoint
Demonstrates how to use the /api/v1/search/similar-laws endpoint

Usage:
    python test_similar_laws_endpoint.py
"""

import requests
import json
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://192.168.100.18:8000"
EMAIL = "your_email@example.com"  # Change this
PASSWORD = "your_password"  # Change this


class SimilarLawsClient:
    """Client for interacting with the Similar Laws API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
    
    def login(self, email: str, password: str) -> bool:
        """
        Authenticate and get JWT token
        
        Args:
            email: User email
            password: User password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('access_token')
                print("✅ Authentication successful!")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def search_similar_laws(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        jurisdiction: str = None,
        law_source_id: int = None
    ) -> Dict[str, Any]:
        """
        Search for similar laws
        
        Args:
            query: Search query text
            top_k: Number of results (1-100)
            threshold: Similarity threshold (0.0-1.0)
            jurisdiction: Optional jurisdiction filter
            law_source_id: Optional law source ID filter
            
        Returns:
            API response dictionary
        """
        if not self.token:
            print("❌ Not authenticated. Please login first.")
            return {}
        
        try:
            # Build query parameters
            params = {
                "query": query,
                "top_k": top_k,
                "threshold": threshold
            }
            
            if jurisdiction:
                params['jurisdiction'] = jurisdiction
            if law_source_id:
                params['law_source_id'] = law_source_id
            
            # Make request
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            print(f"\n🔍 Searching for: '{query}'")
            print(f"   Parameters: top_k={top_k}, threshold={threshold}")
            
            response = requests.post(
                f"{self.base_url}/api/v1/search/similar-laws",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Search successful!")
                return data
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return {}
    
    def print_results(self, response: Dict[str, Any]) -> None:
        """
        Print search results in a readable format
        
        Args:
            response: API response dictionary
        """
        if not response or not response.get('success'):
            print("❌ No results to display")
            return
        
        data = response.get('data', {})
        results = data.get('results', [])
        total = data.get('total_results', 0)
        query = data.get('query', '')
        threshold = data.get('threshold', 0.0)
        
        print(f"\n{'='*80}")
        print(f"📊 SEARCH RESULTS")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Total Results: {total}")
        print(f"Threshold: {threshold}")
        print(f"{'='*80}\n")
        
        for i, result in enumerate(results, 1):
            self._print_result(i, result)
    
    def _print_result(self, index: int, result: Dict[str, Any]) -> None:
        """Print a single search result"""
        print(f"Result #{index}")
        print(f"{'-'*80}")
        
        # Basic info
        print(f"📌 Chunk ID: {result.get('chunk_id')}")
        print(f"⭐ Similarity Score: {result.get('similarity'):.4f}")
        print(f"📝 Content Preview:")
        content = result.get('content', '')[:200]
        print(f"   {content}...")
        print()
        
        # Law metadata
        law_metadata = result.get('law_metadata', {})
        if law_metadata:
            print(f"📚 Law Information:")
            print(f"   • Law Name: {law_metadata.get('law_name')}")
            print(f"   • Law Type: {law_metadata.get('law_type')}")
            print(f"   • Jurisdiction: {law_metadata.get('jurisdiction')}")
            print(f"   • Issue Date: {law_metadata.get('issue_date')}")
            print()
        
        # Article metadata
        article_metadata = result.get('article_metadata', {})
        if article_metadata:
            print(f"📄 Article Information:")
            print(f"   • Article Number: {article_metadata.get('article_number')}")
            print(f"   • Title: {article_metadata.get('title')}")
            if article_metadata.get('keywords'):
                print(f"   • Keywords: {', '.join(article_metadata.get('keywords', []))}")
            print()
        
        # Hierarchy metadata
        branch_metadata = result.get('branch_metadata', {})
        if branch_metadata:
            print(f"📑 Branch: {branch_metadata.get('branch_name')}")
        
        chapter_metadata = result.get('chapter_metadata', {})
        if chapter_metadata:
            print(f"📖 Chapter: {chapter_metadata.get('chapter_name')}")
        
        print(f"{'='*80}\n")


def test_basic_search(client: SimilarLawsClient) -> None:
    """Test basic search functionality"""
    print("\n" + "="*80)
    print("TEST 1: Basic Search")
    print("="*80)
    
    response = client.search_similar_laws(
        query="فسخ عقد العمل",
        top_k=5,
        threshold=0.7
    )
    
    client.print_results(response)


def test_high_precision_search(client: SimilarLawsClient) -> None:
    """Test high precision search"""
    print("\n" + "="*80)
    print("TEST 2: High Precision Search")
    print("="*80)
    
    response = client.search_similar_laws(
        query="حقوق العامل",
        top_k=3,
        threshold=0.85  # Higher threshold for more precise results
    )
    
    client.print_results(response)


def test_filtered_search(client: SimilarLawsClient) -> None:
    """Test search with filters"""
    print("\n" + "="*80)
    print("TEST 3: Filtered Search")
    print("="*80)
    
    response = client.search_similar_laws(
        query="التعويض",
        top_k=5,
        threshold=0.7,
        jurisdiction="المملكة العربية السعودية"
    )
    
    client.print_results(response)


def test_exploratory_search(client: SimilarLawsClient) -> None:
    """Test exploratory search with low threshold"""
    print("\n" + "="*80)
    print("TEST 4: Exploratory Search (Low Threshold)")
    print("="*80)
    
    response = client.search_similar_laws(
        query="عقد",
        top_k=10,
        threshold=0.6  # Lower threshold for broader results
    )
    
    client.print_results(response)


def test_english_query(client: SimilarLawsClient) -> None:
    """Test search with English query"""
    print("\n" + "="*80)
    print("TEST 5: English Query")
    print("="*80)
    
    response = client.search_similar_laws(
        query="employee rights",
        top_k=5,
        threshold=0.7
    )
    
    client.print_results(response)


def get_search_statistics(client: SimilarLawsClient) -> None:
    """Get search statistics"""
    if not client.token:
        print("❌ Not authenticated")
        return
    
    try:
        headers = {"Authorization": f"Bearer {client.token}"}
        response = requests.get(
            f"{client.base_url}/api/v1/search/statistics",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('data', {})
            
            print("\n" + "="*80)
            print("📊 SEARCH STATISTICS")
            print("="*80)
            print(f"Total Searchable Chunks: {stats.get('total_searchable_chunks')}")
            print(f"Law Chunks: {stats.get('law_chunks')}")
            print(f"Case Chunks: {stats.get('case_chunks')}")
            print(f"Cache Size: {stats.get('cache_size')}")
            print(f"Cache Enabled: {stats.get('cache_enabled')}")
            print("="*80 + "\n")
        else:
            print(f"❌ Failed to get statistics: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {str(e)}")


def interactive_mode(client: SimilarLawsClient) -> None:
    """Interactive mode for custom queries"""
    print("\n" + "="*80)
    print("🔍 INTERACTIVE SEARCH MODE")
    print("="*80)
    print("Enter your queries below (or 'quit' to exit)")
    print()
    
    while True:
        try:
            query = input("Enter search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("⚠️  Query cannot be empty")
                continue
            
            # Get optional parameters
            try:
                top_k = input(f"Number of results (default 10): ").strip()
                top_k = int(top_k) if top_k else 10
                
                threshold = input(f"Threshold (default 0.7): ").strip()
                threshold = float(threshold) if threshold else 0.7
            except ValueError:
                print("⚠️  Invalid input, using defaults")
                top_k = 10
                threshold = 0.7
            
            # Perform search
            response = client.search_similar_laws(
                query=query,
                top_k=top_k,
                threshold=threshold
            )
            
            client.print_results(response)
            print("\n" + "-"*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def main():
    """Main function"""
    print("="*80)
    print("🔍 SIMILAR LAWS ENDPOINT TEST SCRIPT")
    print("="*80)
    
    # Create client
    client = SimilarLawsClient(BASE_URL)
    
    # Login
    print("\n🔐 Authenticating...")
    if not client.login(EMAIL, PASSWORD):
        print("\n⚠️  Please update EMAIL and PASSWORD in the script")
        return
    
    # Get statistics
    get_search_statistics(client)
    
    # Run tests
    print("\n📝 Running automated tests...\n")
    
    # Test 1: Basic search
    test_basic_search(client)
    input("\n▶️  Press Enter to continue to next test...")
    
    # Test 2: High precision
    test_high_precision_search(client)
    input("\n▶️  Press Enter to continue to next test...")
    
    # Test 3: Filtered search
    test_filtered_search(client)
    input("\n▶️  Press Enter to continue to next test...")
    
    # Test 4: Exploratory search
    test_exploratory_search(client)
    input("\n▶️  Press Enter to continue to next test...")
    
    # Test 5: English query
    test_english_query(client)
    
    # Interactive mode
    print("\n" + "="*80)
    choice = input("\n🎮 Enter interactive mode? (y/n): ").strip().lower()
    if choice == 'y':
        interactive_mode(client)
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)


if __name__ == "__main__":
    main()


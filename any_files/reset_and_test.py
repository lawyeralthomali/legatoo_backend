"""
Complete workflow test: Reset databases and test upload, generate embeddings, and query
"""
import requests
import time
import shutil
import os

BASE_URL = "http://192.168.100.13:8000"

print("=" * 70)
print("COMPLETE WORKFLOW TEST: Reset -> Login -> Upload -> Generate -> Query")
print("=" * 70)

# Step 0: Clean up old data
print("\n🧹 Step 0: Cleaning up old data...")

# Delete Chroma store
chroma_store = "./chroma_store"
if os.path.exists(chroma_store):
    try:
        shutil.rmtree(chroma_store)
        print(f"✅ Deleted old Chroma store: {chroma_store}")
    except Exception as e:
        print(f"⚠️ Could not delete Chroma store: {e}")

# Clear SQLite database
import sqlite3
db_path = "app.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Delete all data from tables (in correct order to respect foreign keys)
        tables_to_clear = [
            'knowledge_chunks',
            'law_articles',
            'law_sources',
            'knowledge_documents',
            'legal_terms',
            'case_sections',
            'legal_cases'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✅ Cleared table: {table}")
            except Exception as e:
                print(f"  ⚠️ Could not clear table {table}: {e}")
        
        conn.commit()
        conn.close()
        print(f"✅ Cleared SQLite database: {db_path}")
    except Exception as e:
        print(f"⚠️ Could not clear SQLite database: {e}")

# Step 1: Login
print("\n📝 Step 1: Logging in...")
login_data = {
    "email": "legatoo@althomalilawfirm.sa",
    "password": "Zaq1zaq1"
}

try:
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        exit(1)
    
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in successfully")
except Exception as e:
    print(f"❌ Login error: {e}")
    exit(1)

# Step 2: Upload JSON file
print("\n📤 Step 2: Uploading JSON file...")
try:
    with open("data_set/files/saudi_labor_law.json", "rb") as f:
        files = {"file": ("saudi_labor_law.json", f, "application/json")}
        upload_data = {
            "title": "نظام العمل السعودي",
            "category": "law"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/laws/upload-json",
            headers=headers,
            files=files,
            data=upload_data,
            timeout=60
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed ({response.status_code}): {response.text[:500]}")
        exit(1)
    
    upload_result = response.json()
    print(f"✅ Upload successful!")
    print(f"   Response: {upload_result.get('message', 'N/A')}")
    
    # Get document ID from response (it's the law_source.id)
    law_source_id = None
    document_id = None
    if upload_result.get('success'):
        data = upload_result.get('data', {})
        # Try to get law_source.id
        law_source = data.get('law_source', {})
        law_source_id = law_source.get('id')
    
    if law_source_id:
        print(f"   Law Source ID: {law_source_id}")
    else:
        print(f"❌ Could not find law_source.id in response")
        print(f"   Response keys: {list(upload_result.keys())}")
        print(f"   Data keys: {list(upload_result.get('data', {}).keys())}")
        exit(1)
    
    # We need to get the knowledge_document_id from the database
    # The law_source has a foreign key to knowledge_document
    import sqlite3
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT knowledge_document_id FROM law_sources WHERE id = ?", (law_source_id,))
    row = cursor.fetchone()
    if row:
        document_id = row[0]
        print(f"✅ Found Knowledge Document ID: {document_id}")
    else:
        print(f"❌ Could not find knowledge_document_id for law_source {law_source_id}")
        exit(1)
    conn.close()
    
except Exception as e:
    print(f"❌ Upload error: {e}")
    exit(1)

# Wait for processing
time.sleep(3)

# Step 3: Generate embeddings
print("\n🔮 Step 3: Generating embeddings...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/laws/{document_id}/generate-embeddings",
        headers=headers,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Generate embeddings failed ({response.status_code}): {response.text[:500]}")
        exit(1)
    
    embeddings_result = response.json()
    print(f"✅ Embeddings generated!")
    print(f"   Message: {embeddings_result.get('message', 'N/A')}")
    
except Exception as e:
    print(f"❌ Generate embeddings error: {e}")
    exit(1)

# Wait for embeddings
time.sleep(3)

# Step 4: Query
print("\n🔍 Step 4: Querying...")
query = "المادة الاولى من نظام العمل"
query_params = {"query": query, "top_k": 5}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/laws/query",
        headers=headers,
        params=query_params,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Query failed ({response.status_code}): {response.text[:500]}")
        exit(1)
    
    query_result = response.json()
    print(f"✅ Query successful!")
    
    if query_result.get('success'):
        data = query_result.get('data', {})
        results_count = data.get('results_count', 0)
        print(f"   Results: {results_count}")
        print(f"   Message: {data.get('message', 'N/A')}")
        
        if results_count > 0:
            print(f"\n📄 First result:")
            chunks = data.get('chunks', [])
            if chunks:
                first_chunk = chunks[0]
                print(f"   - Article: {first_chunk.get('article_number', 'N/A')}")
                print(f"   - Law: {first_chunk.get('law_name', 'N/A')}")
                print(f"   - Score: {first_chunk.get('score', 'N/A'):.4f}")
                content = first_chunk.get('content', '')
                print(f"   - Content preview: {content[:100]}...")
    else:
        print(f"   Success: False")
        print(f"   Message: {query_result.get('message', 'N/A')}")
        
except Exception as e:
    print(f"❌ Query error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)

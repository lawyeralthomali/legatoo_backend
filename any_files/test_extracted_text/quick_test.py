import urllib.request
import json

try:
    # Test if endpoint exists
    req = urllib.request.Request('http://localhost:8000/api/v1/rag/upload-document')
    req.get_method = lambda: 'GET'
    
    try:
        response = urllib.request.urlopen(req, timeout=10)
        print(f"GET response: {response.status}")
        print(f"Content: {response.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"GET HTTP Error: {e.code} - {e.reason}")
        if e.code == 405:  # Method Not Allowed
            print("SUCCESS: Endpoint exists but expects POST (this is correct)")
        else:
            print(f"Unexpected error: {e.read().decode()}")
    except Exception as e:
        print(f"GET Error: {e}")

    # Test POST with minimal data
    print("\n--- Testing POST ---")
    
    # Create a simple text file
    with open('test.txt', 'w', encoding='utf-8') as f:
        f.write('Test document content')
    
    # Simple multipart form
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    with open('test.txt', 'rb') as f:
        file_content = f.read()
    
    data = f'--{boundary}\r\n'
    data += 'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    data += 'Content-Type: text/plain\r\n\r\n'
    data = data.encode() + file_content + b'\r\n'
    data += f'--{boundary}\r\n'.encode()
    data += 'Content-Disposition: form-data; name="law_name"\r\n\r\n'.encode()
    data += 'Test Law\r\n'.encode()
    data += f'--{boundary}\r\n'.encode()
    data += 'Content-Disposition: form-data; name="law_type"\r\n\r\n'.encode()
    data += 'law\r\n'.encode()
    data += f'--{boundary}\r\n'.encode()
    data += 'Content-Disposition: form-data; name="jurisdiction"\r\n\r\n'.encode()
    data += 'Saudi Arabia\r\n'.encode()
    data += f'--{boundary}--\r\n'.encode()
    
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/rag/upload-document',
        data=data,
        method='POST'
    )
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        response = urllib.request.urlopen(req, timeout=30)
        print(f"POST Success: {response.status}")
        result = json.loads(response.read().decode())
        print(f"Response: {json.dumps(result, indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"POST HTTP Error: {e.code} - {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"Error details: {error_body}")
        except:
            print("Could not read error body")
    except Exception as e:
        print(f"POST Error: {e}")

except Exception as e:
    print(f"General error: {e}")
finally:
    # Clean up
    import os
    if os.path.exists('test.txt'):
        os.remove('test.txt')
        print("Cleaned up test file")

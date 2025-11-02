# 🔧 Frontend Task: Fix Legal Cases List API Call (405 Method Not Allowed)

## 🐛 Problem

The frontend is receiving a **405 Method Not Allowed** error when trying to fetch the list of legal cases:

```http
GET /api/v1/legal-cases HTTP/1.1
Response: 405 Method Not Allowed
```

## 📋 Context

The backend has a valid GET endpoint for listing legal cases, but there might be an issue with:
1. **Route path mismatch** (trailing slash issue)
2. **HTTP method** used in the frontend
3. **Route ordering** in FastAPI
4. **CORS or middleware** blocking the request

## ✅ Correct API Endpoint

### List Legal Cases (GET)
```http
GET /api/v1/legal-cases/
Authorization: Bearer YOUR_TOKEN
```

**Note:** The endpoint might require a trailing slash `/` depending on how FastAPI is configured.

### Query Parameters (Optional)
```
?skip=0                      # Number of records to skip (default: 0)
&limit=50                    # Maximum records to return (default: 50)
&jurisdiction=الرياض        # Filter by jurisdiction
&case_type=عمل              # Filter by case type: مدني, جنائي, تجاري, عمل, إداري
&court_level=ابتدائي        # Filter by court level: ابتدائي, استئناف, تمييز, عالي
&status=processed            # Filter by status: raw, processed, indexed
&search=case_title           # Search in case title or case number
```

### Response (Success)
```json
{
  "success": true,
  "message": "Legal cases retrieved successfully",
  "data": {
    "cases": [
      {
        "id": 1,
        "case_number": "123/2024",
        "title": "قضية عمالية - إنهاء خدمات",
        "description": "نزاع حول إنهاء خدمات عامل بدون مبرر",
        "jurisdiction": "الرياض",
        "court_name": "المحكمة العمالية بالرياض",
        "decision_date": "2024-01-15",
        "case_type": "عمل",
        "court_level": "ابتدائي",
        "status": "processed",
        "created_at": "2024-01-20T10:00:00",
        "updated_at": "2024-01-20T10:00:00",
        "knowledge_document_id": 456
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  },
  "errors": []
}
```

### Response (Error - Not Authenticated)
```json
{
  "success": false,
  "message": "Not authenticated",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "Invalid or missing authentication token"
    }
  ]
}
```

## 🎯 Solution Steps

### Step 1: Check Refactor Your API Call Function

First, make sure you're using the correct endpoint path:

```typescript
// ✅ CORRECT - Try with trailing slash first
const fetchLegalCases = async (filters?: {
  skip?: number;
  limit?: number;
  jurisdiction?: string;
  case_type?: string;
  court_level?: string;
  status?: string;
  search?: string;
}) => {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters?.jurisdiction) params.append('jurisdiction', filters.jurisdiction);
    if (filters?.case_type) params.append('case_type', filters.case_type);
    if (filters?.court_level) params.append('court_level', filters.court_level);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.search) params.append('search', filters.search);
    
    const queryString = params.toString();
    const url = `/api/v1/legal-cases/${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      // Handle HTTP errors
      if (response.status === 405) {
        // Try with trailing slash if 405 error
        const urlWithSlash = `/api/v1/legal-cases/${queryString ? `?${queryString}` : ''}`;
        const retryResponse = await fetch(urlWithSlash, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!retryResponse.ok) {
          throw new Error(`HTTP ${retryResponse.status}: ${retryResponse.statusText}`);
        }
        
        return await retryResponse.json();
      }
      
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch legal cases');
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching legal cases:', error);
    throw error;
  }
};
```

### Step 2: Alternative - Use Axios (If Available)

If you're using Axios, it might handle trailing slashes better:

```typescript
import axios from 'axios';

const fetchLegalCases = async (filters?: {
  skip?: number;
  limit?: number;
  jurisdiction?: string;
  case_type?: string;
  court_level?: string;
  status?: string;
  PKsearch?: string;
}) => {
  try {
    const response = await axios.get('/api/v1/legal-cases/', {
      params: filters,
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.message || 'Failed to fetch legal cases');
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 405) {
        // Retry without trailing slash
        const response = await axios.get('/api/v1/legal-cases', {
          params: filters,
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        });
        return response.data;
      }
      throw new Error(error.response?.data?.message || error.message);
    }
    throw error;
  }
};
```

### Step 3: Check Your API Client Configuration

If you have a centralized API client, make sure it's configured correctly:

```typescript
// api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = {
  get: async (endpoint: string, params?: Record<string, any>) => {
    const url = new URL(endpoint, API_BASE_URL);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    // Ensure trailing slash for root endpoints
    if (endpoint.endsWith('/legal-cases')) {
      url.pathname = url.pathname + '/';
    }
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  }
};

// Usage
export const fetchLegalCases = (filters?: any) => {
  return apiClient.get('/api/v1/legal-cases/', filters);
};
```

### Step 4: Debug the Actual Request

Add debugging to see what's actually being sent:

```typescript
const fetchLegalCases = async (filters?: any) => {
  const url = `/api/v1/legal-cases/`;
  console.log('🌐 Fetching legal cases from:', url);
  console.log('📋 Filters:', filters);
  console.log('🔑 Auth token:', getAuthToken() ? 'Present' : 'Missing');
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('📡 Response status:', response.status);
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('✅ Success response:', data);
    return data;
  } catch (error) {
    console.error('💥 Fetch error:', error);
    throw error;
  }
};
```

### Step 5: Check Network Tab

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Clear the network log
4. Trigger the API call
5. Look for the request to `/api/v1/legal-cases`
6. Check:
   - **Request URL**: Exact path being called
   - **Request Method**: Should be `GET`
   - **Status Code**: Current status (405)
   - **Request Headers**: Check if `Authorization` header is present
   - **Response**: What the server is returning

## 🔍 Common Issues and Fixes

### Issue 1: Missing Trailing Slash
**Symptom:** 405 error on `/api/v1/legal-cases` (no trailing slash)
**Fix:** Add trailing slash: `/api/v1/legal-cases/`

### Issue 2: Wrong HTTP Method
**Symptom:** Using POST or other method instead of GET
**Fix:** Ensure `method: 'GET'` in fetch options

### Issue 3: Missing Authentication
**Symptom:** 401 or 405 (some servers return 405 for auth issues)
**Fix:** Ensure `Authorization: Bearer <token>` header is present

### Issue 4: CORS Preflight
**Symptom:** 405 on OPTIONS preflight request
**Fix:** Backend should handle OPTIONS requests (already configured)

### Issue 5: Route Conflict
**Symptom:** Route matches `/api/v1/legal-cases/{case_id}` instead of `/api/v1/legal-cases/`
**Fix:** Ensure exact path matching (back-end should handle this, but check route order)

## 🧪 Testing Checklist

- [ ] API call uses correct endpoint `/api/v1/legal-cases/` (with trailing slash)
- [ ] HTTP method is `GET` (not POST, PUT, etc.)
- [ ] Authorization header is present with valid token
- [ ] Content-Type header is `application/json`
- [ ] Network tab shows correct request URL and method
- [ ] No CORS errors in console
- [ ] Try both with and without trailing slash to find which works
- [ ] Check backend logs to see what route is being hit

## 💻 Component Example

Here's a complete React component example:

```tsx
'use client';

import { useState, useEffect } from 'react';

interface LegalCase {
  id: number;
  case_number: string;
  title: string;
  description?: string;
  jurisdiction?: string;
  court_name?: string;
  decision_date?: string;
  case_type?: string;
  court_level?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface LegalCasesListProps {
  language: 'ar' | 'en';
}

export function LegalCasesList({ language }: LegalCasesListProps) {
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchCases();
  }, []);
  
  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try with trailing slash first
      let url = '/api/v1/legal-cases/';
      let response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      // If 405, try without trailing slash
      if (response.status === 405) {
        url = '/api/v1/legal-cases';
        response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setCases(data.data.cases || data.data || []);
      } else {
        throw new Error(data.message || 'Failed to fetch legal cases');
      }
    } catch (err) {
      console.error('Error fetching legal cases:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner">⏳</div>
        <p>{language === 'ar' ? 'جاري التحميل...' : 'Loading...'}</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">❌ {error}</p>
        <button onClick={fetchCases}>
          {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
        </button>
      </div>
    );
  }
  
  return (
    <div className="legal-cases-list">
      <h2>{language === 'ar' ? 'القضايا القانونية' : 'Legal Cases'}</h2>
      
      {cases.length === 0 ? (
        <p>{language === 'ar' ? 'لا توجد قضايا' : 'No cases found'}</p>
      ) : (
        <table className="cases-table">
          <thead>
            <tr>
              <th>{language === 'ar' ? 'رقم القضية' : 'Case Number'}</th>
              <th>{language === 'ar' ? 'العنوان' : 'Title'}</th>
              <th>{language === 'ar' ? 'النوع' : 'Type'}</th>
              <th>{language === 'ar' ? 'الاختصاص' : 'Jurisdiction'}</th>
              <th>{language === 'ar' ? 'الحالة' : 'Status'}</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((case) => (
              <tr key={case.id}>
                <td>{case.case_number}</td>
                <td>{case.title}</td>
                <td>{case.case_type}</td>
                <td>{case.jurisdiction}</td>
                <td>
                  <span className={`status-badge status-${case.status}`}>
                    {case.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// Helper function to get auth token
function getAuthToken(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('auth_token') || '';
}
```

## 🚨 Quick Fix (Try This First)

The fastest fix is to ensure you're using the exact endpoint path with proper method:

```typescript
// Replace your current fetch call with this:
const response = await fetch('/api/v1/legal-cases/', {
  method: 'GET',  // ← Make sure it's GET, not POST
  headers: {
    'Authorization': `Bearer ${yourAuthToken}`,
    'Content-Type': 'application/json'
  }
});
```

## 📌 Key Points

1. **Endpoint Path**: `/api/v1/legal-cases/` (with trailing slash) or `/api/v1/legal-cases` (without)
2. **HTTP Method**: Must be `GET`
3. **Authentication**: Must include `Authorization: Bearer <token>` header
4. **Content-Type**: Should be `application/json`
5. **Error Handling**: Check for both 405 and try alternative paths

## 🔗 Related Endpoints

If the list endpoint works, you can also use:

- **Get Single Case**: `GET /api/v1/legal-cases/{case_id}`
- **Upload Case**: `POST /api/v1/legal-cases/upload`
- **Update Case**: `PUT /api/v1/legal-cases/{case_id}`
- **Delete Case**: `DELETE /api/v1/legal-cases/{case_id}`
- **Get Case Sections**: `GET /api/v1/legal-cases/{case_id}/sections`

## 🆘 Still Having Issues?

If the problem persists after trying the above:

1. **Check Backend Logs**: Look for what route is actually being hit
2. **Test with Postman/Thunder Client**: Verify the endpoint works outside of frontend
3. **Check Browser Console**: Look戊for any JavaScript errors or network errors
4. **Verify CORS**: Ensure CORS is configured correctly for your frontend URL
5. **Check Route Registration**: Verify the router is registered correctly in backend

Good luck! 🎯

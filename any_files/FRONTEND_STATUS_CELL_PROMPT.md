# 🎯 Frontend Task: Implement Clickable Status Cell for Law Table

## 📋 Context

You have a table displaying a list of laws with the following structure:
- Law name
- Type
- Jurisdiction
- **Status** (this is the cell we need to make interactive)
- Other metadata

## 🎯 Goal

Make the **Status** cell interactive when the status is `raw` (unprocessed):
1. Display status with appropriate styling and translation
2. When status is `raw`, make it **clickable** with a button or badge
3. On click, call the embedding generation API
4. **Immediately** update the UI to show "جاري المعالجة" (Processing) in Arabic or "Processing" in English
5. The actual embedding generation runs in background on the server

## 📊 Current API Endpoints

### 1. List Laws (GET)
```http
GET /api/v1/laws?page=1&page_size=20&status=raw
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 5 laws",
  "data": {
    "laws": [
      {
        "id": 123,
        "name": "نظام العمل السعودي",
        "type": "law",
        "jurisdiction": "المملكة العربية السعودية",
        "issuing_authority": "وزارة العمل",
        "status": "raw",  // "raw", "processing", or "processed"
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "total_pages": 1
    }
  }
}
```

### 2. Generate Embeddings (POST)
```http
POST /api/v1/laws/{document_id}/generate-embeddings
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Embedding generation started in background for document 123",
  "data": {
    "document_id": 123,
    "status": "processing",
    "message": "Embeddings are being generated in the background. Check logs for progress."
  }
}
```

### 3. Get Single Law (Optional - for polling status)
```http
GET /api/v1/laws/{law_id}
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "message": "Law metadata retrieved successfully",
  "data": {
    "id": 123,
    "name": "نظام العمل السعودي",
    "status": "processed",  // Updated status
    ...
  }
}
```

## 🎨 UI/UX Requirements

### Status Display Mapping

| Status | Arabic | English | Color | Icon | Clickable |
|--------|--------|---------|-------|------|-----------|
| `raw` | غير معالج | Unprocessed | 🟡 Yellow/Warning | ⚠️ | ✅ Yes |
| `processing` | جاري المعالجة | Processing | 🔵 Blue/Info | ⏳ | ❌ No |
| `processed` | معالج | Processed | 🟢 Green/Success | ✅ | ❌ No |

### Interaction Flow

1. **Initial State:** Status = `raw`
   - Display: Badge/Button with "غير معالج" (yellow)
   - Text: "انقر للمعالجة" (Click to process)
   - Cursor: pointer

2. **On Click:**
   - **Immediately** update UI to show "جاري المعالجة" (blue, loading spinner)
   - Call API: `POST /api/v1/laws/{document_id}/generate-embeddings`
   - Disable the button/badge (no more clicks)

3. **Background Processing:**
   - Embeddings are generated on the server
   - Optionally: Poll every 10-30 seconds to check if status changed to `processed`
   - Or: Use WebSocket/SSE for real-time updates (if available)

4. **Final State:** Status = `processed`
   - Display: Badge with "معالج" (green, checkmark)
   - No interaction needed

## 💻 Implementation Guide

### Step 1: Create Status Component

Create a reusable `StatusBadge` component that:
- Takes `status`, `lawId`, `documentId`, and `language` as props
- Displays appropriate text, color, and icon
- Makes it clickable when status is `raw`
- Handles the click event and API call

**Example (React/TypeScript):**

```tsx
interface StatusBadgeProps {
  status: 'raw' | 'processing' | 'processed';
  lawId: number;
  documentId: number;
  language: 'ar' | 'en';
  onStatusChange?: (newStatus: string) => void;
}

function StatusBadge({ status, lawId, documentId, language, onStatusChange }: StatusBadgeProps) {
  const [currentStatus, setCurrentStatus] = useState(status);
  const [isLoading, setIsLoading] = useState(false);
  
  const statusConfig = {
    raw: {
      ar: { label: 'غير معالج', hint: 'انقر للمعالجة' },
      en: { label: 'Unprocessed', hint: 'Click to process' }
    },
    processing: {
      ar: { label: 'جاري المعالجة', hint: 'يتم المعالجة في الخلفية' },
      en: { label: 'Processing', hint: 'Processing in background' }
    },
    processed: {
      ar: { label: 'معالج', hint: 'جاهز للاستخدام' },
      en: { label: 'Processed', hint: 'Ready to use' }
    }
  };
  
  const config = statusConfig[currentStatus][language];
  
  const handleClick = async () => {
    if (currentStatus !== 'raw' || isLoading) return;
    
    try {
      // Step 1: Immediately update UI (optimistic update)
      setCurrentStatus('processing');
      setIsLoading(true);
      if (onStatusChange) onStatusChange('processing');
      
      // Step 2: Call API
      const response = await fetch(`/api/v1/laws/${documentId}/generate-embeddings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Status already updated in UI
        console.log('✅ Embedding generation started');
        
        // Optional: Poll for completion
        // startPollingStatus(documentId);
      } else {
        // Revert on error
        setCurrentStatus('raw');
        setIsLoading(false);
        if (onStatusChange) onStatusChange('raw');
        alert(`Failed: ${result.message}`);
      }
      
    } catch (error) {
      // Revert on error
      setCurrentStatus('raw');
      setIsLoading(false);
      if (onStatusChange) onStatusChange('raw');
      console.error('Error generating embeddings:', error);
      alert('Failed to start embedding generation');
    }
  };
  
  const getStatusColor = () => {
    switch (currentStatus) {
      case 'raw': return 'warning'; // yellow
      case 'processing': return 'info'; // blue
      case 'processed': return 'success'; // green
    }
  };
  
  const getStatusIcon = () => {
    switch (currentStatus) {
      case 'raw': return '⚠️';
      case 'processing': return isLoading ? '⏳' : '🔄';
      case 'processed': return '✅';
    }
  };
  
  return (
    <div className="status-badge-wrapper">
      <button
        onClick={handleClick}
        disabled={currentStatus !== 'raw'}
        className={`badge badge-${getStatusColor()} ${currentStatus === 'raw' ? 'clickable' : ''}`}
        title={config.hint}
      >
        <span className="icon">{getStatusIcon()}</span>
        <span className="label">{config.label}</span>
        {isLoading && <span className="spinner">⏳</span>}
      </button>
    </div>
  );
}
```

### Step 2: Integrate into Table

```tsx
function LawsTable({ laws, language }: { laws: Law[], language: 'ar' | 'en' }) {
  const [lawsData, setLawsData] = useState(laws);
  
  const handleStatusChange = (lawId: number, newStatus: string) => {
    // Update local state
    setLawsData(prev => 
      prev.map(law => 
        law.id === lawId ? { ...law, status: newStatus } : law
      )
    );
  };
  
  return (
    <table className="laws-table">
      <thead>
        <tr>
          <th>{language === 'ar' ? 'اسم القانون' : 'Law Name'}</th>
          <th>{language === 'ar' ? 'النوع' : 'Type'}</th>
          <th>{language === 'ar' ? 'الاختصاص' : 'Jurisdiction'}</th>
          <th>{language === 'ar' ? 'الحالة' : 'Status'}</th>
          <th>{language === 'ar' ? 'الإجراءات' : 'Actions'}</th>
        </tr>
      </thead>
      <tbody>
        {lawsData.map(law => (
          <tr key={law.id}>
            <td>{law.name}</td>
            <td>{law.type}</td>
            <td>{law.jurisdiction}</td>
            <td>
              <StatusBadge
                status={law.status}
                lawId={law.id}
                documentId={law.knowledge_document_id || law.id}
                language={language}
                onStatusChange={(newStatus) => handleStatusChange(law.id, newStatus)}
              />
            </td>
            <td>
              {/* Other actions */}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### Step 3: Add CSS Styling

```css
.status-badge-wrapper {
  display: inline-block;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.badge.clickable {
  cursor: pointer;
  border: 1px solid currentColor;
}

.badge.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.badge-warning {
  background-color: #fef3c7;
  color: #92400e;
}

.badge-info {
  background-color: #dbeafe;
  color: #1e40af;
}

.badge-success {
  background-color: #d1fae5;
  color: #065f46;
}

.badge:disabled,
.badge.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

## 🔄 Optional: Status Polling

If you want to automatically update status when processing completes:

```typescript
function useStatusPolling(documentId: number, initialStatus: string) {
  const [status, setStatus] = useState(initialStatus);
  
  useEffect(() => {
    if (status !== 'processing') return;
    
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/laws/${documentId}`, {
          headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        });
        const result = await response.json();
        
        if (result.data.status === 'processed') {
          setStatus('processed');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 10000); // Poll every 10 seconds
    
    return () => clearInterval(pollInterval);
  }, [documentId, status]);
  
  return status;
}
```

## 📝 Key Points to Remember

1. **Optimistic UI Update**: Update status to "processing" IMMEDIATELY on click, don't wait for API response
2. **Error Handling**: Revert to "raw" if API call fails
3. **Disable on Processing**: Don't allow clicking when status is "processing" or "processed"
4. **Language Support**: Show Arabic or English based on current language setting
5. **Visual Feedback**: Use colors, icons, and tooltips to make status clear
6. **Background Processing**: The server handles embeddings in background, frontend just triggers it

## 🐛 Testing Checklist

- [ ] Status "raw" displays correctly with yellow/warning color
- [ ] Status cell is clickable when status is "raw"
- [ ] Clicking changes status to "processing" immediately
- [ ] API call is made to `/generate-embeddings` endpoint
- [ ] Status stays "processing" even after page refresh (fetched from API)
- [ ] Status eventually changes to "processed" (check manually or via polling)
- [ ] Error handling works (try with invalid token or document ID)
- [ ] Works in both Arabic and English
- [ ] Responsive design works on mobile/tablet
- [ ] Loading spinner shows during API call

## 🎨 UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│  القوانين (Laws)                                                │
├─────────────────────────────────────────────────────────────────┤
│  اسم القانون     │ النوع  │ الاختصاص      │ الحالة             │
├─────────────────────────────────────────────────────────────────┤
│  نظام العمل      │ قانون  │ السعودية      │ [⚠️ غير معالج ⬅️] │ ← Clickable!
│  نظام التجارة    │ قانون  │ السعودية      │ [⏳ جاري المعالجة]│
│  نظام الشركات    │ قانون  │ السعودية      │ [✅ معالج]         │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Summary

Create a clickable status badge that:
1. Shows current status with appropriate styling
2. When clicked (and status is `raw`):
   - Updates UI to "جاري المعالجة" / "Processing" immediately
   - Calls API to generate embeddings
   - Disables further clicks
3. Handles errors gracefully
4. Supports both Arabic and English

**The key is the OPTIMISTIC UI UPDATE** - change the status in the UI immediately when clicked, don't wait for the server!

Good luck! 🎯


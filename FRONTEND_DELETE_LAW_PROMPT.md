# 🗑️ Frontend Task: Implement Delete Law Functionality

## 📋 Context

You have a table displaying a list of laws. Each row needs a **Delete** button that allows users to delete a law from both the SQL database and the Chroma vectorstore.

## 🎯 Goal

Add a delete button for each law in the table that:
1. Shows a **confirmation dialog** before deletion (prevent accidental deletion)
2. Calls the DELETE API endpoint
3. Shows loading state during deletion
4. Updates the table immediately after successful deletion (optimistic UI)
5. Shows success/error notifications
6. Handles errors gracefully

## 📊 Current API Endpoint

### Delete Law (DELETE)
```http
DELETE /api/v1/laws/{law_id}
Authorization: Bearer YOUR_TOKEN
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Law 'نظام العمل السعودي' deleted successfully from both databases",
  "data": {
    "deleted_law_id": 123,
    "deleted_law_name": "نظام العمل السعودي",
    "deleted_chunks_count": 245,
    "knowledge_document_id": 456
  }
}
```

**Response (Error - Not Found):**
```json
{
  "success": false,
  "message": "Law with ID 123 not found",
  "data": null,
  "errors": []
}
```

**Response (Error - Server):**
```json
{
  "success": false,
  "message": "Failed to delete law: Database error",
  "data": null,
  "errors": []
}
```

## 🎨 UI/UX Requirements

### Delete Button Design

```
┌────────────────────────────────────────────────────────┐
│  نظام العمل  │ قانون │ معالج │ [✅ Edit] [🗑️ Delete] │
└────────────────────────────────────────────────────────┘
```

**Button States:**

| State | Icon | Color | Cursor | Disabled |
|-------|------|-------|--------|----------|
| Normal | 🗑️ | Red | pointer | No |
| Hover | 🗑️ | Dark Red | pointer | No |
| Deleting | ⏳ | Gray | wait | Yes |
| Disabled | 🗑️ | Light Gray | not-allowed | Yes |

### Confirmation Dialog

**Important:** Always show a confirmation dialog to prevent accidental deletion!

**Arabic Dialog:**
```
┌─────────────────────────────────────────┐
│  ⚠️  تأكيد الحذف                        │
├─────────────────────────────────────────┤
│                                         │
│  هل أنت متأكد من حذف القانون:          │
│  "نظام العمل السعودي"؟                 │
│                                         │
│  سيتم حذف:                             │
│  • جميع المواد (245 مادة)              │
│  • جميع البيانات المرتبطة              │
│  • محتوى قاعدة البيانات                │
│                                         │
│  ⚠️  لا يمكن التراجع عن هذا الإجراء!   │
│                                         │
│  [إلغاء]            [حذف نهائياً]      │
└─────────────────────────────────────────┘
```

**English Dialog:**
```
┌─────────────────────────────────────────┐
│  ⚠️  Confirm Deletion                   │
├─────────────────────────────────────────┤
│                                         │
│  Are you sure you want to delete:      │
│  "Saudi Labor Law"?                    │
│                                         │
│  This will delete:                     │
│  • All articles (245 articles)         │
│  • All related data                    │
│  • Database content                    │
│                                         │
│  ⚠️  This action cannot be undone!     │
│                                         │
│  [Cancel]            [Delete Forever]  │
└─────────────────────────────────────────┘
```

## 💻 Implementation Guide

### Step 1: Create DeleteButton Component

```tsx
interface DeleteButtonProps {
  lawId: number;
  lawName: string;
  articlesCount?: number;
  chunksCount?: number;
  language: 'ar' | 'en';
  onDeleteSuccess?: () => void;
  onDeleteError?: (error: string) => void;
}

function DeleteButton({
  lawId,
  lawName,
  articlesCount = 0,
  chunksCount = 0,
  language,
  onDeleteSuccess,
  onDeleteError
}: DeleteButtonProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  
  const t = {
    ar: {
      deleteBtn: 'حذف',
      confirmTitle: 'تأكيد الحذف',
      confirmMessage: 'هل أنت متأكد من حذف القانون:',
      willDelete: 'سيتم حذف:',
      allArticles: 'جميع المواد',
      allData: 'جميع البيانات المرتبطة',
      dbContent: 'محتوى قاعدة البيانات',
      warning: '⚠️ لا يمكن التراجع عن هذا الإجراء!',
      cancel: 'إلغاء',
      confirmDelete: 'حذف نهائياً',
      deleting: 'جاري الحذف...',
      successMsg: 'تم حذف القانون بنجاح',
      errorMsg: 'فشل حذف القانون'
    },
    en: {
      deleteBtn: 'Delete',
      confirmTitle: 'Confirm Deletion',
      confirmMessage: 'Are you sure you want to delete:',
      willDelete: 'This will delete:',
      allArticles: 'All articles',
      allData: 'All related data',
      dbContent: 'Database content',
      warning: '⚠️ This action cannot be undone!',
      cancel: 'Cancel',
      confirmDelete: 'Delete Forever',
      deleting: 'Deleting...',
      successMsg: 'Law deleted successfully',
      errorMsg: 'Failed to delete law'
    }
  };
  
  const text = t[language];
  
  const handleDelete = async () => {
    setIsDeleting(true);
    
    try {
      const response = await fetch(`/api/v1/laws/${lawId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Success!
        showNotification(text.successMsg, 'success');
        setShowConfirm(false);
        
        // Notify parent component
        if (onDeleteSuccess) {
          onDeleteSuccess();
        }
        
        // Log the deletion details
        console.log('Deleted:', result.data);
        
      } else {
        // API returned error
        throw new Error(result.message || text.errorMsg);
      }
      
    } catch (error) {
      console.error('Delete error:', error);
      showNotification(`${text.errorMsg}: ${error.message}`, 'error');
      
      if (onDeleteError) {
        onDeleteError(error.message);
      }
      
    } finally {
      setIsDeleting(false);
    }
  };
  
  return (
    <>
      {/* Delete Button */}
      <button
        onClick={() => setShowConfirm(true)}
        disabled={isDeleting}
        className="btn btn-danger btn-sm"
        title={text.deleteBtn}
      >
        <span className="icon">🗑️</span>
        <span className="label">{text.deleteBtn}</span>
      </button>
      
      {/* Confirmation Dialog */}
      {showConfirm && (
        <ConfirmDialog
          isOpen={showConfirm}
          onClose={() => setShowConfirm(false)}
          onConfirm={handleDelete}
          title={text.confirmTitle}
          isLoading={isDeleting}
          language={language}
        >
          <div className="confirm-content">
            <p className="confirm-question">
              {text.confirmMessage}
            </p>
            <p className="law-name">"{lawName}"</p>
            
            <div className="deletion-details">
              <p className="will-delete-title">{text.willDelete}</p>
              <ul>
                <li>• {text.allArticles} ({articlesCount} {language === 'ar' ? 'مادة' : 'articles'})</li>
                <li>• {text.allData}</li>
                <li>• {text.dbContent}</li>
              </ul>
            </div>
            
            <div className="warning-box">
              {text.warning}
            </div>
          </div>
        </ConfirmDialog>
      )}
    </>
  );
}
```

### Step 2: Create ConfirmDialog Component

```tsx
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  isLoading: boolean;
  language: 'ar' | 'en';
  children: React.ReactNode;
}

function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  isLoading,
  language,
  children
}: ConfirmDialogProps) {
  const t = {
    ar: { cancel: 'إلغاء', confirm: 'حذف نهائياً', deleting: 'جاري الحذف...' },
    en: { cancel: 'Cancel', confirm: 'Delete Forever', deleting: 'Deleting...' }
  };
  
  const text = t[language];
  
  if (!isOpen) return null;
  
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog-box" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="dialog-header">
          <h3>{title}</h3>
          <button className="close-btn" onClick={onClose} disabled={isLoading}>
            ✕
          </button>
        </div>
        
        {/* Content */}
        <div className="dialog-content">
          {children}
        </div>
        
        {/* Footer */}
        <div className="dialog-footer">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            {text.cancel}
          </button>
          
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="btn btn-danger"
          >
            {isLoading ? (
              <>
                <span className="spinner">⏳</span>
                {text.deleting}
              </>
            ) : (
              <>
                <span className="icon">🗑️</span>
                {text.confirm}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Step 3: Integrate into Laws Table

```tsx
interface Law {
  id: number;
  name: string;
  type: string;
  jurisdiction: string;
  status: string;
  knowledge_document_id: number;
  // ... other fields
}

function LawsTable({ language }: { language: 'ar' | 'en' }) {
  const [laws, setLaws] = useState<Law[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch laws on mount
  useEffect(() => {
    fetchLaws();
  }, []);
  
  const fetchLaws = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/laws?page=1&page_size=50', {
        headers: { 'Authorization': `Bearer ${getAuthToken()}` }
      });
      const result = await response.json();
      
      if (result.success) {
        setLaws(result.data.laws);
      }
    } catch (error) {
      console.error('Failed to fetch laws:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteSuccess = (deletedLawId: number) => {
    // Optimistic UI update - remove law from list immediately
    setLaws(prev => prev.filter(law => law.id !== deletedLawId));
    
    // Optionally refetch to ensure sync
    // fetchLaws();
  };
  
  return (
    <div className="laws-table-container">
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
          {laws.map(law => (
            <tr key={law.id}>
              <td>{law.name}</td>
              <td>{law.type}</td>
              <td>{law.jurisdiction}</td>
              <td>
                <StatusBadge
                  status={law.status}
                  lawId={law.id}
                  documentId={law.knowledge_document_id}
                  language={language}
                />
              </td>
              <td className="actions-cell">
                {/* Edit Button */}
                <button
                  onClick={() => handleEdit(law.id)}
                  className="btn btn-primary btn-sm"
                >
                  <span className="icon">✏️</span>
                  {language === 'ar' ? 'تعديل' : 'Edit'}
                </button>
                
                {/* Delete Button */}
                <DeleteButton
                  lawId={law.id}
                  lawName={law.name}
                  articlesCount={law.articles_count || 0}
                  language={language}
                  onDeleteSuccess={() => handleDeleteSuccess(law.id)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {isLoading && <LoadingSpinner />}
      
      {!isLoading && laws.length === 0 && (
        <EmptyState message={language === 'ar' ? 'لا توجد قوانين' : 'No laws found'} />
      )}
    </div>
  );
}
```

### Step 4: Add CSS Styling

```css
/* Delete Button */
.btn-danger {
  background-color: #dc2626;
  color: white;
  border: 1px solid #dc2626;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-danger:hover:not(:disabled) {
  background-color: #b91c1c;
  border-color: #b91c1c;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
}

.btn-danger:disabled {
  background-color: #d1d5db;
  border-color: #d1d5db;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Dialog Overlay */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.dialog-box {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 90%;
  animation: slideUp 0.3s ease;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0.25rem;
}

.close-btn:hover {
  color: #111827;
}

.dialog-content {
  padding: 1.5rem;
}

.confirm-question {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.law-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1rem;
}

.deletion-details {
  background-color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
}

.will-delete-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.deletion-details ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.deletion-details li {
  padding: 0.25rem 0;
  color: #4b5563;
}

.warning-box {
  background-color: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 0.375rem;
  padding: 0.75rem;
  color: #92400e;
  font-weight: 500;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

## 🔄 User Flow

```
User sees law list
    │
    ▼
User clicks 🗑️ Delete button
    │
    ▼
┌─────────────────────────────────┐
│  ⚠️  Confirmation Dialog Opens  │
│  Shows law name & details       │
│  Warns about permanent deletion │
└─────────────────────────────────┘
    │
    ├─→ User clicks "Cancel" → Dialog closes, nothing happens
    │
    └─→ User clicks "Delete Forever"
         │
         ▼
    Button shows loading (⏳ Deleting...)
         │
         ▼
    API call to DELETE /api/v1/laws/{law_id}
         │
         ├─→ Success
         │    │
         │    ▼
         │   ✅ Show success notification
         │   ✅ Remove law from table (optimistic update)
         │   ✅ Close dialog
         │
         └─→ Error
              │
              ▼
             ❌ Show error notification
             ❌ Keep law in table
             ❌ Keep dialog open
```

## 🧪 Testing Checklist

- [ ] Delete button appears for each law in the table
- [ ] Clicking delete shows confirmation dialog
- [ ] Dialog displays law name correctly
- [ ] Dialog shows warning message
- [ ] Cancel button closes dialog without deleting
- [ ] Delete button shows loading state during API call
- [ ] Successful deletion removes law from table
- [ ] Successful deletion shows success notification
- [ ] Error shows error notification and keeps law in table
- [ ] Dialog can be closed by clicking outside (overlay)
- [ ] Dialog cannot be closed while deleting (loading state)
- [ ] Works in both Arabic and English
- [ ] Responsive design works on mobile
- [ ] Keyboard accessibility (ESC to close, Enter to confirm)

## 🔒 Permissions & Security

### Optional: Role-Based Access Control

If you want to restrict deletion to admins only:

```tsx
function DeleteButton({ lawId, lawName, currentUser, ... }: DeleteButtonProps) {
  // Only show delete button for admins
  if (currentUser.role !== 'admin' && currentUser.role !== 'super_admin') {
    return null;
  }
  
  // ... rest of component
}
```

### Optional: Soft Delete UI

For extra safety, you could add a "Trash" feature where deleted laws are moved to trash first:

```tsx
// First delete: Move to trash (soft delete)
// Second delete: Permanent deletion from trash
```

## 📌 Key Points to Remember

1. **Always show confirmation** - Never delete without asking!
2. **Optimistic UI** - Remove from table immediately on success
3. **Loading states** - Show spinner during deletion
4. **Error handling** - Show clear error messages
5. **Notifications** - Give user feedback on success/failure
6. **Bilingual** - Support both Arabic and English
7. **Accessibility** - Keyboard support and screen readers
8. **Mobile friendly** - Responsive dialog design

## 🚀 Summary

Implement a delete button that:
- ✅ Shows confirmation dialog (prevent accidents)
- ✅ Calls DELETE API endpoint
- ✅ Shows loading state
- ✅ Updates UI optimistically
- ✅ Handles errors gracefully
- ✅ Works in both languages
- ✅ Provides clear user feedback

Good luck! 🎯


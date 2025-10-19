# 🔧 Fix: Profile to User Relationship Migration

## المشكلة | Problem

**Error**:
```
Could not determine join condition between parent/child tables on 
relationship Profile.uploaded_documents - there are no foreign keys 
linking these tables.
```

## السبب | Root Cause

كان موديل `Profile` يحتوي على علاقة `uploaded_documents` تشير إلى `LegalDocument`:

```python
# ❌ WRONG - في Profile
uploaded_documents = relationship("LegalDocument", back_populates="uploaded_by")
```

لكن موديل `LegalDocument` تم تحديثه ليرتبط بـ `User` مباشرة:

```python
# ✅ CORRECT - في LegalDocument
uploaded_by_id = Column(Integer, ForeignKey("users.id"))
uploaded_by = relationship("User", back_populates="uploaded_documents")
```

**النتيجة**: تعارض في العلاقات - `Profile` يحاول الربط لكن لا يوجد Foreign Key!

---

## الحل | Solution

### ✅ تم إزالة العلاقة من Profile

**قبل**:
```python
# app/models/profile.py
class Profile(Base):
    # ...
    user = relationship("User", back_populates="profile")
    uploaded_documents = relationship("LegalDocument", back_populates="uploaded_by")  # ❌
```

**بعد**:
```python
# app/models/profile.py
class Profile(Base):
    # ...
    user = relationship("User", back_populates="profile")
    # Note: uploaded_documents relationship moved to User model
    # Legal documents are now linked to User, not Profile
```

---

## العلاقات الصحيحة | Correct Relationships

### 1. User ↔ LegalDocument

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    
    # Relationships
    uploaded_documents = relationship(
        "LegalDocument",
        back_populates="uploaded_by",
        lazy="select"
    )
```

```python
# app/models/legal_document2.py
class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    uploaded_by = relationship(
        "User",
        back_populates="uploaded_documents",
        lazy="select"
    )
```

### 2. User ↔ Profile

```python
# app/models/user.py
class User(Base):
    profile = relationship("Profile", back_populates="user", uselist=False)
```

```python
# app/models/profile.py
class Profile(Base):
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="profile")
```

---

## التسلسل الهرمي | Hierarchy

```
User (users table)
  │
  ├─── Profile (profiles table)           [1:1 relationship]
  │     └── user_id → users.id
  │
  └─── LegalDocument (legal_documents)    [1:N relationship]
        └── uploaded_by_id → users.id
```

**ملاحظة**: `Profile` لم يعد له علاقة مباشرة مع `LegalDocument`

---

## كيفية الوصول | How to Access

### الوصول إلى المستندات من User

```python
# ✅ مباشرة
user = db.query(User).filter(User.id == 1).first()
documents = user.uploaded_documents  # List of LegalDocument

for doc in documents:
    print(f"Document: {doc.title}")
```

### الوصول إلى المستندات من Profile

```python
# ✅ عبر User
profile = db.query(Profile).filter(Profile.id == 1).first()
documents = profile.user.uploaded_documents  # عبر العلاقة مع User

for doc in documents:
    print(f"Document: {doc.title}")
```

### الوصول إلى الـ User من Document

```python
# ✅ مباشرة
document = db.query(LegalDocument).filter(LegalDocument.id == 1).first()
user = document.uploaded_by  # User object

print(f"Uploaded by: {user.email}")
print(f"User profile: {user.profile.first_name}")  # ومنه للـ Profile
```

---

## الملفات المُعدّلة | Modified Files

1. ✅ `app/models/profile.py` - إزالة علاقة `uploaded_documents`
2. ✅ `app/models/user.py` - إضافة علاقة `uploaded_documents`
3. ✅ `app/models/legal_document2.py` - تحديث FK و relationship

---

## الاختبار | Testing

### Test 1: إنشاء مستند

```python
from app.models.user import User
from app.models.legal_document2 import LegalDocument, DocumentTypeEnum

# Get user
user = db.query(User).filter(User.email == "test@example.com").first()

# Create document
doc = LegalDocument(
    title="Test Document",
    file_path="test.pdf",
    uploaded_by_id=user.id,  # ✅ User ID
    document_type=DocumentTypeEnum.OTHER
)
db.add(doc)
db.commit()

# Verify relationship
assert doc.uploaded_by.id == user.id
assert doc in user.uploaded_documents
```

### Test 2: الوصول من Profile

```python
from app.models.profile import Profile

# Get profile
profile = db.query(Profile).filter(Profile.user_id == user.id).first()

# Access documents via user
docs = profile.user.uploaded_documents  # ✅ Works!
assert len(docs) > 0
```

---

## الحالة | Status

| البند | الحالة |
|------|--------|
| إزالة علاقة Profile | ✅ مكتمل |
| تحديث علاقة User | ✅ مكتمل |
| تحديث LegalDocument FK | ✅ مكتمل |
| اختبار الخادم | ✅ يعمل |
| حل خطأ Mapper | ✅ محلول |

---

## الخلاصة | Summary

✅ **المشكلة**: علاقة `Profile.uploaded_documents` بدون Foreign Key  
✅ **الحل**: إزالة العلاقة من Profile، الاحتفاظ بها في User فقط  
✅ **النتيجة**: العلاقات صحيحة، الخادم يعمل، لا أخطاء!  

**الآن**: المستندات مرتبطة بـ `User` مباشرة، ويمكن الوصول إليها من `Profile` عبر `profile.user.uploaded_documents`

---

**Last Updated**: October 2, 2025  
**Fixed By**: AI Assistant  
**Status**: ✅ Resolved


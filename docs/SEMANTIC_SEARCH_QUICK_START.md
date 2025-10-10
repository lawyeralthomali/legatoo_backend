# 🚀 دليل البدء السريع - نظام البحث الدلالي
# Semantic Search - Quick Start Guide

## ⏱️ ابدأ في 5 دقائق!

---

## ✅ المتطلبات الأساسية

قبل البدء، تأكد من:
- [x] نظام الـ Embeddings مثبت ويعمل
- [x] تم إنشاء embeddings للبيانات (818 chunks)
- [x] السيرفر يعمل على `http://localhost:8000`
- [x] لديك JWT token للمصادقة

---

## 📦 الخطوة 1: التحقق من الإعداد

### 1️⃣ تشغيل السيرفر
```bash
cd C:\Users\Lenovo\my_project
py run.py
```

### 2️⃣ التحقق من أن API جاهز
```bash
curl http://localhost:8000/docs
```
يجب أن ترى واجهة Swagger UI

### 3️⃣ التحقق من إحصائيات البحث
```bash
curl -X GET "http://localhost:8000/api/v1/search/statistics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**النتيجة المتوقعة**:
```json
{
  "success": true,
  "data": {
    "total_searchable_chunks": 818,
    "law_chunks": 600,
    "case_chunks": 218,
    "cache_enabled": true
  }
}
```

---

## 🔍 الخطوة 2: أول بحث لك

### بحث بسيط في القوانين

**PowerShell**:
```powershell
$token = "YOUR_JWT_TOKEN_HERE"
$query = "فسخ عقد العمل"

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/search/similar-laws?query=$query&top_k=5&threshold=0.7" `
  -Headers @{ Authorization = "Bearer $token" }
```

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/search/similar-laws?query=فسخ+عقد+العمل&top_k=5&threshold=0.7" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python**:
```python
import requests

url = "http://localhost:8000/api/v1/search/similar-laws"
params = {
    "query": "فسخ عقد العمل",
    "top_k": 5,
    "threshold": 0.7
}
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

response = requests.post(url, params=params, headers=headers)
print(response.json())
```

---

## 📊 الخطوة 3: استكشاف جميع الميزات

### 1️⃣ بحث في القضايا
```bash
curl -X POST "http://localhost:8000/api/v1/search/similar-cases?query=إنهاء+خدمات+عامل&case_type=عمل&top_k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2️⃣ بحث هجين (قوانين + قضايا)
```bash
curl -X POST "http://localhost:8000/api/v1/search/hybrid?query=حقوق+العامل&search_types=laws,cases&top_k=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3️⃣ اقتراحات تلقائية
```bash
curl -X GET "http://localhost:8000/api/v1/search/suggestions?partial_query=نظام+ال&limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🎯 أمثلة الاستخدام الشائعة

### مثال 1: بحث عن مواد قانونية محددة
```python
import requests

def search_laws(query_text):
    url = "http://localhost:8000/api/v1/search/similar-laws"
    params = {
        "query": query_text,
        "top_k": 10,
        "threshold": 0.75,
        "jurisdiction": "السعودية"  # اختياري
    }
    headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
    
    response = requests.post(url, params=params, headers=headers)
    data = response.json()
    
    if data['success']:
        print(f"✅ Found {data['data']['total_results']} laws")
        for result in data['data']['results']:
            print(f"\n📜 Similarity: {result['similarity']:.2f}")
            print(f"📄 {result['content'][:200]}...")
            if 'law_metadata' in result:
                print(f"📚 Source: {result['law_metadata']['law_name']}")
    else:
        print(f"❌ Error: {data['message']}")

# استخدام
search_laws("الإجازات السنوية للعامل")
```

### مثال 2: بحث في السوابق القضائية
```python
def search_cases(query_text, case_type=None):
    url = "http://localhost:8000/api/v1/search/similar-cases"
    params = {
        "query": query_text,
        "top_k": 5,
        "threshold": 0.7
    }
    
    if case_type:
        params['case_type'] = case_type
    
    headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
    response = requests.post(url, params=params, headers=headers)
    data = response.json()
    
    if data['success']:
        print(f"✅ Found {data['data']['total_results']} cases")
        for result in data['data']['results']:
            case_meta = result.get('case_metadata', {})
            print(f"\n⚖️ Case: {case_meta.get('case_number', 'N/A')}")
            print(f"🏛️ Court: {case_meta.get('court_name', 'N/A')}")
            print(f"📊 Similarity: {result['similarity']:.2f}")
    else:
        print(f"❌ Error: {data['message']}")

# استخدام
search_cases("تعويض عن فصل تعسفي", case_type="عمل")
```

### مثال 3: بحث شامل (Hybrid)
```python
def comprehensive_search(query_text):
    url = "http://localhost:8000/api/v1/search/hybrid"
    params = {
        "query": query_text,
        "search_types": "laws,cases",
        "top_k": 5,
        "threshold": 0.6
    }
    headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
    
    response = requests.post(url, params=params, headers=headers)
    data = response.json()
    
    if data['success']:
        result_data = data['data']
        print(f"🔍 Total Results: {result_data['total_results']}\n")
        
        # عرض القوانين
        if 'laws' in result_data and result_data['laws']['count'] > 0:
            print(f"📜 LAWS ({result_data['laws']['count']}):")
            for law in result_data['laws']['results'][:3]:
                print(f"  - {law['content'][:100]}...")
                print(f"    Similarity: {law['similarity']:.2f}\n")
        
        # عرض القضايا
        if 'cases' in result_data and result_data['cases']['count'] > 0:
            print(f"⚖️ CASES ({result_data['cases']['count']}):")
            for case in result_data['cases']['results'][:3]:
                print(f"  - {case['content'][:100]}...")
                print(f"    Similarity: {case['similarity']:.2f}\n")
    else:
        print(f"❌ Error: {data['message']}")

# استخدام
comprehensive_search("المسؤولية التقصيرية")
```

---

## 🌐 اختبار من Swagger UI

1. افتح المتصفح: `http://localhost:8000/docs`
2. اضغط على **Authorize** 🔒
3. أدخل JWT Token: `Bearer YOUR_TOKEN`
4. اختبر أي endpoint:
   - `/api/v1/search/similar-laws`
   - `/api/v1/search/similar-cases`
   - `/api/v1/search/hybrid`
   - `/api/v1/search/suggestions`
   - `/api/v1/search/statistics`

---

## 📱 مثال: واجهة بحث بسيطة (React)

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function SearchInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/search/hybrid',
        null,
        {
          params: {
            query,
            search_types: 'laws,cases',
            top_k: 5,
            threshold: 0.7
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      setResults(response.data.data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <h2>🔍 البحث القانوني الذكي</h2>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="ابحث في القوانين والقضايا..."
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'جاري البحث...' : 'بحث'}
      </button>

      {results.total_results > 0 && (
        <div className="results">
          <h3>النتائج ({results.total_results})</h3>
          
          {results.laws && results.laws.count > 0 && (
            <div className="laws-section">
              <h4>📜 القوانين ({results.laws.count})</h4>
              {results.laws.results.map((law, i) => (
                <div key={i} className="result-card">
                  <p>{law.content.substring(0, 200)}...</p>
                  <span className="similarity">
                    تشابه: {(law.similarity * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}

          {results.cases && results.cases.count > 0 && (
            <div className="cases-section">
              <h4>⚖️ القضايا ({results.cases.count})</h4>
              {results.cases.results.map((caseItem, i) => (
                <div key={i} className="result-card">
                  <p>{caseItem.content.substring(0, 200)}...</p>
                  <span className="similarity">
                    تشابه: {(caseItem.similarity * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchInterface;
```

---

## 🧪 اختبار شامل

قم بنسخ هذا السكريبت لاختبار جميع الميزات:

```python
"""
test_semantic_search.py - اختبار شامل لنظام البحث الدلالي
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/search"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # ضع الـ token الخاص بك
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_statistics():
    """اختبار الإحصائيات"""
    print("\n" + "="*50)
    print("📊 Testing Statistics...")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/statistics", headers=HEADERS)
    data = response.json()
    
    if data['success']:
        stats = data['data']
        print(f"✅ Total Searchable Chunks: {stats['total_searchable_chunks']}")
        print(f"✅ Law Chunks: {stats['law_chunks']}")
        print(f"✅ Case Chunks: {stats['case_chunks']}")
        print(f"✅ Cache Enabled: {stats['cache_enabled']}")
    else:
        print(f"❌ Failed: {data['message']}")


def test_similar_laws():
    """اختبار البحث في القوانين"""
    print("\n" + "="*50)
    print("📜 Testing Similar Laws Search...")
    print("="*50)
    
    params = {
        "query": "فسخ عقد العمل بدون إنذار",
        "top_k": 3,
        "threshold": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/similar-laws", params=params, headers=HEADERS)
    data = response.json()
    
    if data['success']:
        print(f"✅ Found: {data['data']['total_results']} laws")
        for i, result in enumerate(data['data']['results'], 1):
            print(f"\n{i}. Similarity: {result['similarity']:.2f}")
            print(f"   Content: {result['content'][:150]}...")
    else:
        print(f"❌ Failed: {data['message']}")


def test_similar_cases():
    """اختبار البحث في القضايا"""
    print("\n" + "="*50)
    print("⚖️ Testing Similar Cases Search...")
    print("="*50)
    
    params = {
        "query": "تعويض عن فصل تعسفي",
        "top_k": 3,
        "threshold": 0.7,
        "case_type": "عمل"
    }
    
    response = requests.post(f"{BASE_URL}/similar-cases", params=params, headers=HEADERS)
    data = response.json()
    
    if data['success']:
        print(f"✅ Found: {data['data']['total_results']} cases")
        for i, result in enumerate(data['data']['results'], 1):
            print(f"\n{i}. Similarity: {result['similarity']:.2f}")
            print(f"   Content: {result['content'][:150]}...")
    else:
        print(f"❌ Failed: {data['message']}")


def test_hybrid_search():
    """اختبار البحث الهجين"""
    print("\n" + "="*50)
    print("🔄 Testing Hybrid Search...")
    print("="*50)
    
    params = {
        "query": "حقوق العامل في الإجازات",
        "search_types": "laws,cases",
        "top_k": 2,
        "threshold": 0.6
    }
    
    response = requests.post(f"{BASE_URL}/hybrid", params=params, headers=HEADERS)
    data = response.json()
    
    if data['success']:
        result_data = data['data']
        print(f"✅ Total Results: {result_data['total_results']}")
        if 'laws' in result_data:
            print(f"   📜 Laws: {result_data['laws']['count']}")
        if 'cases' in result_data:
            print(f"   ⚖️ Cases: {result_data['cases']['count']}")
    else:
        print(f"❌ Failed: {data['message']}")


def test_suggestions():
    """اختبار الاقتراحات"""
    print("\n" + "="*50)
    print("💡 Testing Search Suggestions...")
    print("="*50)
    
    params = {
        "partial_query": "نظام ال",
        "limit": 5
    }
    
    response = requests.get(f"{BASE_URL}/suggestions", params=params, headers=HEADERS)
    data = response.json()
    
    if data['success']:
        suggestions = data['data']['suggestions']
        print(f"✅ Found {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
    else:
        print(f"❌ Failed: {data['message']}")


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🎯"*25)
    print("🚀 Starting Semantic Search Tests")
    print("🎯"*25)
    
    test_statistics()
    test_similar_laws()
    test_similar_cases()
    test_hybrid_search()
    test_suggestions()
    
    print("\n" + "="*50)
    print("✅ All Tests Completed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    run_all_tests()
```

**تشغيل الاختبار**:
```bash
python test_semantic_search.py
```

---

## 🎓 نصائح للاستخدام الأمثل

### 1️⃣ اختيار threshold المناسب
```python
# للبحث الواسع (نتائج أكثر، دقة أقل)
threshold = 0.5

# للبحث المتوازن (الأفضل للاستخدام العام)
threshold = 0.7

# للبحث الدقيق جداً (نتائج أقل، دقة عالية)
threshold = 0.85
```

### 2️⃣ استخدام الفلاتر بحكمة
```python
# بحث عام - بطيء لكن شامل
results = search_service.find_similar_laws(query)

# بحث محدد - أسرع وأدق
results = search_service.find_similar_laws(
    query,
    filters={'law_source_id': 1, 'jurisdiction': 'السعودية'}
)
```

### 3️⃣ معالجة النتائج
```python
for result in results:
    # التحقق من وجود البيانات الوصفية
    if 'law_metadata' in result:
        law_name = result['law_metadata']['law_name']
    
    # استخدام درجة التشابه للفلترة
    if result['similarity'] > 0.8:
        # نتيجة عالية الدقة
        pass
```

---

## ✅ قائمة التحقق النهائية

قبل الانتقال للإنتاج، تأكد من:
- [ ] السيرفر يعمل بدون أخطاء
- [ ] جميع الـ embeddings تم إنشاؤها (818/818)
- [ ] اختبرت جميع الـ endpoints
- [ ] النتائج دقيقة ومفيدة
- [ ] أوقات الاستجابة مقبولة (< 2 ثانية)
- [ ] التعامل مع الأخطاء يعمل بشكل صحيح

---

## 🚀 الخطوات التالية

بعد إتقان نظام البحث، يمكنك:
1. **دمجه مع Legal Assistant** لتحليل قانوني ذكي
2. **بناء Chatbot** يستخدم البحث للإجابة على الأسئلة
3. **إنشاء Dashboard** للإحصائيات والتحليلات
4. **تطوير Mobile App** للبحث القانوني أثناء التنقل

---

## 📞 المساعدة

إذا واجهت مشاكل:
1. راجع `docs/SEMANTIC_SEARCH_COMPLETE_GUIDE.md` للتفاصيل الكاملة
2. تحقق من `logs/app.log` للأخطاء
3. استخدم Swagger UI للاختبار: `http://localhost:8000/docs`

---

**🎉 مبروك! أنت الآن جاهز لاستخدام نظام البحث الدلالي!** 🚀

"""
Comprehensive Search Test Script
يختبر البحث في جميع القوانين المضافة ويحفظ النتائج في ملف
"""

import sys
import asyncio
import json
from datetime import datetime
from sqlalchemy import select

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_search_service import ArabicLegalSearchService


class SearchTester:
    def __init__(self):
        self.results = []
        self.test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def run_comprehensive_test(self):
        """يشغل اختبارات شاملة على جميع القوانين"""
        
        async with AsyncSessionLocal() as db:
            print("🚀 بدء الاختبار الشامل للبحث...")
            print("=" * 80)
            
            # تهيئة خدمة البحث (uses default sts-arabert)
            search_service = ArabicLegalSearchService(
                db, 
                # model_name not specified = uses default 'sts-arabert'
                use_faiss=False
            )
            search_service.embedding_service.initialize_model()
            
            # اختبارات متنوعة
            test_cases = [
                # مجموعة ١: اختبارات التزوير (موجودة في النظام الجزائي)
                {
                    "category": "التزوير والأختام",
                    "tests": [
                        {"query": "عقوبة تزوير خاتم الدولة أو الملك", "threshold": 0.7},
                        {"query": "تزوير خاتم الملك", "threshold": 0.5},
                        {"query": "خاتم الدولة المزور", "threshold": 0.5},
                        {"query": "تزوير طابع", "threshold": 0.7},
                        {"query": "تزوير أوراق تجارية", "threshold": 0.7},
                        {"query": "عقوبة التزوير والتقليد", "threshold": 0.6},
                    ]
                },
                
                # مجموعة ٢: اختبارات العلامات التجارية (موجودة في نظام العلامات)
                {
                    "category": "العلامات التجارية",
                    "tests": [
                        {"query": "العلامة التجارية", "threshold": 0.7},
                        {"query": "تسجيل علامة تجارية", "threshold": 0.6},
                        {"query": "تزوير علامة تجارية", "threshold": 0.7},
                        {"query": "مدة حماية العلامة", "threshold": 0.5},
                        {"query": "شطب العلامة التجارية", "threshold": 0.5},
                    ]
                },
                
                # مجموعة ٣: اختبارات نظام العمل (موجودة في نظام العمل)
                {
                    "category": "نظام العمل",
                    "tests": [
                        {"query": "عقد العمل", "threshold": 0.7},
                        {"query": "أجر العامل", "threshold": 0.6},
                        {"query": "إنهاء عقد العمل", "threshold": 0.6},
                        {"query": "إجازة سنوية", "threshold": 0.5},
                        {"query": "ساعات العمل", "threshold": 0.6},
                        {"query": "توظيف السعوديين", "threshold": 0.7},
                    ]
                },
                
                # مجموعة ٤: اختبارات عامة عبر القوانين
                {
                    "category": "اختبارات عامة",
                    "tests": [
                        {"query": "عقوبة السجن", "threshold": 0.5},
                        {"query": "الغرامة المالية", "threshold": 0.5},
                        {"query": "التعويض عن الأضرار", "threshold": 0.5},
                        {"query": "تزوير وتقليد", "threshold": 0.6},
                    ]
                }
            ]
            
            # تشغيل جميع الاختبارات
            total_tests = sum(len(category["tests"]) for category in test_cases)
            current_test = 1
            
            for category in test_cases:
                print(f"\n📂 فئة: {category['category']}")
                print("-" * 50)
                
                for test in category["tests"]:
                    print(f"🔍 اختبار {current_test}/{total_tests}: '{test['query']}' (عتبة: {test['threshold']})")
                    
                    try:
                        results = await search_service.find_similar_laws(
                            query=test['query'],
                            top_k=5,
                            threshold=test['threshold']
                        )
                        
                        # حفظ النتائج
                        test_result = {
                            "test_number": current_test,
                            "category": category['category'],
                            "query": test['query'],
                            "threshold": test['threshold'],
                            "total_results": len(results),
                            "results": results,
                            "success": len(results) > 0
                        }
                        
                        self.results.append(test_result)
                        
                        # عرض النتائج المختصرة
                        if results:
                            best_result = results[0]
                            print(f"   ✅ وجد {len(results)} نتيجة - أفضل تشابه: {best_result['similarity']:.4f}")
                            if 'article_metadata' in best_result:
                                print(f"   📄 أفضل نتيجة: {best_result['article_metadata']['article_number']} - {best_result['article_metadata']['title']}")
                        else:
                            print(f"   ❌ لم توجد نتائج (العتبة: {test['threshold']})")
                            
                    except Exception as e:
                        print(f"   💥 خطأ: {str(e)}")
                        self.results.append({
                            "test_number": current_test,
                            "category": category['category'], 
                            "query": test['query'],
                            "threshold": test['threshold'],
                            "error": str(e),
                            "success": False
                        })
                    
                    current_test += 1
            
            # حفظ النتائج في ملف
            await self.save_results_to_file()
            
            # عرض إحصائيات
            await self.show_statistics()

    async def save_results_to_file(self):
        """يحفظ النتائج في ملف نصي و JSON"""
        
        # حفظ كـ JSON
        json_filename = f"search_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "test_date": self.test_date,
                "total_tests": len(self.results),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        # حفظ كـ نص مقروء
        txt_filename = f"search_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("📊 نتائج الاختبار الشامل للبحث الدلالي\n")
            f.write("=" * 80 + "\n")
            f.write(f"📅 تاريخ الاختبار: {self.test_date}\n")
            f.write(f"🔢 عدد الاختبارات: {len(self.results)}\n\n")
            
            successful_tests = [r for r in self.results if r.get('success')]
            failed_tests = [r for r in self.results if not r.get('success')]
            
            f.write(f"✅ الاختبارات الناجحة: {len(successful_tests)}\n")
            f.write(f"❌ الاختبارات الفاشلة: {len(failed_tests)}\n")
            f.write(f"📈 نسبة النجاح: {(len(successful_tests)/len(self.results))*100:.1f}%\n\n")
            
            # التفاصيل
            for result in self.results:
                f.write(f"\n{'='*60}\n")
                f.write(f"🔍 اختبار #{result['test_number']}: {result['query']}\n")
                f.write(f"📂 الفئة: {result['category']}\n")
                f.write(f"🎯 العتبة: {result['threshold']}\n")
                
                if result.get('success'):
                    f.write(f"✅ النتائج: {result['total_results']}\n")
                    
                    for i, res in enumerate(result['results'], 1):
                        f.write(f"\n   {i}. التشابه: {res['similarity']:.4f}\n")
                        f.write(f"      المحتوى: {res['content'][:100]}...\n")
                        if 'article_metadata' in res:
                            f.write(f"      المادة: {res['article_metadata']['article_number']} - {res['article_metadata']['title']}\n")
                        if 'law_metadata' in res:
                            f.write(f"      القانون: {res['law_metadata']['law_name']}\n")
                else:
                    f.write(f"❌ لم توجد نتائج\n")
                    if result.get('error'):
                        f.write(f"💥 الخطأ: {result['error']}\n")
                
                f.write(f"{'-'*60}\n")
        
        print(f"\n💾 تم حفظ النتائج في:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📝 TXT: {txt_filename}")

    async def show_statistics(self):
        """يعرض إحصائيات الاختبار"""
        
        successful_tests = [r for r in self.results if r.get('success')]
        failed_tests = [r for r in self.results if not r.get('success')]
        
        print(f"\n{'='*80}")
        print(f"📊 إحصائيات الاختبار الشامل")
        print(f"{'='*80}")
        print(f"📅 تاريخ الاختبار: {self.test_date}")
        print(f"🔢 إجمالي الاختبارات: {len(self.results)}")
        print(f"✅ الاختبارات الناجحة: {len(successful_tests)}")
        print(f"❌ الاختبارات الفاشلة: {len(failed_tests)}")
        print(f"📈 نسبة النجاح: {(len(successful_tests)/len(self.results))*100:.1f}%")
        
        # إحصائيات حسب الفئة
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'success': 0}
            categories[cat]['total'] += 1
            if result.get('success'):
                categories[cat]['success'] += 1
        
        print(f"\n📂 الإحصائيات حسب الفئة:")
        for cat, stats in categories.items():
            success_rate = (stats['success']/stats['total'])*100 if stats['total'] > 0 else 0
            print(f"   {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # أفضل التشابهات
        all_similarities = []
        for result in successful_tests:
            for res in result['results']:
                all_similarities.append(res['similarity'])
        
        if all_similarities:
            print(f"\n🎯 إحصائيات التشابه:")
            print(f"   🔼 أعلى تشابه: {max(all_similarities):.4f}")
            print(f"   🔽 أقل تشابه: {min(all_similarities):.4f}")
            print(f"   📊 متوسط التشابه: {sum(all_similarities)/len(all_similarities):.4f}")
        
        print(f"\n💡 التوصيات:")
        if len(failed_tests) > len(self.results) * 0.3:
            print("   ⚠️  نسبة الفشل عالية - جرب خفض العتبة إلى 0.4 أو 0.3")
        else:
            print("   ✅ الأداء جيد - يمكن تحسين النموذج لتحقيق دقة أعلى")


async def check_database_content():
    """يتحقق من محتوى قاعدة البيانات"""
    
    async with AsyncSessionLocal() as db:
        print("\n🔍 التحقق من محتوى قاعدة البيانات...")
        
        # عدد الـ chunks
        from app.models.legal_knowledge import KnowledgeChunk, LawSource
        from sqlalchemy import func
        
        # إحصائيات عامة
        total_chunks = await db.execute(select(func.count(KnowledgeChunk.id)))
        total_chunks_count = total_chunks.scalar()
        
        chunks_with_embeddings = await db.execute(
            select(func.count(KnowledgeChunk.id))
            .where(KnowledgeChunk.embedding_vector.isnot(None))
        )
        embeddings_count = chunks_with_embeddings.scalar()
        
        # القوانين المتاحة
        laws = await db.execute(
            select(LawSource.name, func.count(KnowledgeChunk.id))
            .join(KnowledgeChunk, LawSource.id == KnowledgeChunk.law_source_id)
            .group_by(LawSource.name)
        )
        
        print(f"📊 إحصائيات قاعدة البيانات:")
        print(f"   📦 إجمالي الـ chunks: {total_chunks_count}")
        print(f"   🤖 الـ chunks ذات الـ embeddings: {embeddings_count}")
        print(f"   📈 نسبة التغطية: {(embeddings_count/total_chunks_count)*100:.1f}%" if total_chunks_count > 0 else "N/A")
        
        print(f"\n📚 القوانين المتاحة:")
        for law_name, chunk_count in laws.all():
            print(f"   📖 {law_name}: {chunk_count} chunks")


async def main():
    """الدالة الرئيسية"""
    
    print("🚀 بدء الاختبار الشامل لنظام البحث الدلالي")
    print("=" * 80)
    
    # التحقق من قاعدة البيانات
    await check_database_content()
    
    # تشغيل الاختبارات
    tester = SearchTester()
    await tester.run_comprehensive_test()
    
    print(f"\n🎉 اكتمل الاختبار الشامل!")
    print("📁 تم حفظ النتائج في ملفات يمكنك تحليلها")


if __name__ == "__main__":
    asyncio.run(main())
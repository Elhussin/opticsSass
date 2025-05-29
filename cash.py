from django.core.cache import cache

def clear_all_cache():
    cache.clear()
    print("✅ تم مسح جميع ملفات الكاش بنجاح!")


clear_all_cache()

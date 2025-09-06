from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


# Утилита для получения данных из кеша или выполнения запроса к БД
def get_cached_data(cache_key, queryset_func, timeout=60 * 15):
    data = cache.get(cache_key)
    if data is None:
        logger.info(f"Cache MISS for key: {cache_key}")
        data = queryset_func()
        cache.set(cache_key, data, timeout)
    else:
        logger.info(f"Cache HIT for key: {cache_key}")
    return data


# Утилита для инвалидации кеша по шаблону
def invalidate_cache(cache_key_pattern):
    keys = cache.keys(cache_key_pattern)
    if keys:
        cache.delete_many(keys)

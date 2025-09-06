from django.core.cache import cache
from functools import wraps
import hashlib
import json
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def cache_per_user(timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # ключ на основе URL и пользователя
            path = request.build_absolute_uri()
            user_id = request.user.id if request.user.is_authenticated else "anonymous"
            cache_key = (
                f"view_cache_{user_id}_{hashlib.md5(path.encode('utf-8')).hexdigest()}"
            )
            # получить данные из кеша
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"View Cache HIT for key: {cache_key}")
                # Восстанав. Response из кешированных данных
                return Response(
                    data=cached_data["data"],
                    status=cached_data["status"],
                    headers=cached_data["headers"],
                )
            logger.info(f"View Cache MISS for key: {cache_key}")
            response = view_func(request, *args, **kwargs)
            # Получаем данные из response для кеширования
            cache_data = {
                "data": response.data,
                "status": response.status_code,
                "headers": dict(response.headers),
            }
            cache.set(cache_key, cache_data, timeout)
            return response
        return _wrapped_view
    return decorator

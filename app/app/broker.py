from taskiq import TaskiqMiddleware
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from app.core.config import settings

result_backend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL,
    result_ex_time=3600,
)

broker = RedisStreamBroker(
    url=settings.REDIS_URL,
).with_result_backend(result_backend)

import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.redis import RedisCachePersistenceLayer

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379)
config = IdempotencyConfig(expires_after_seconds=1)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    sleep_time: int = event.get("sleep") or 0
    time.sleep(sleep_time)

    return event

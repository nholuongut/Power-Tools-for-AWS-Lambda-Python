from __future__ import annotations

from typing import Any

from redis import Redis

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
)

redis_values: dict[str, Any] = parameters.get_secret("redis_info", transform="json")  # (1)!

redis_client = Redis(
    host=redis_values.get("REDIS_HOST", "localhost"),
    port=redis_values.get("REDIS_PORT", 6379),
    password=redis_values.get("REDIS_PASSWORD"),
    decode_responses=True,
    socket_timeout=10.0,
    ssl=True,
    retry_on_timeout=True,
)

persistence_layer = RedisCachePersistenceLayer(client=redis_client)
config = IdempotencyConfig(
    expires_after_seconds=2 * 60,  # 2 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "Hello"}

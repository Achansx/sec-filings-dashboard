"""
Rate limiter for SEC API requests using Redis.

Implements a token bucket algorithm to comply with SEC EDGAR's
rate limiting requirements (10 requests per second).
"""
import asyncio
import logging
import time
from typing import Optional
from functools import wraps

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitException(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SECRateLimiter:
    """
    Token bucket rate limiter for SEC API requests.

    Implements rate limiting using Redis to ensure compliance with
    SEC EDGAR's 10 requests per second limit. The implementation is
    distributed-safe, allowing multiple workers to share the same limit.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        rate_limit: int = 10,
        window_seconds: int = 1,
        key_prefix: str = "sec_ratelimit",
    ):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
            rate_limit: Maximum requests per window (default: 10)
            window_seconds: Time window in seconds (default: 1)
            key_prefix: Redis key prefix for rate limit tracking
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self._redis: Optional[aioredis.Redis] = None

        logger.info(
            f"Initialized SEC rate limiter: {rate_limit} requests per {window_seconds}s"
        )

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def acquire(self, tokens: int = 1, timeout: Optional[float] = 10.0) -> bool:
        """
        Acquire tokens from the rate limiter.

        Uses a sliding window algorithm implemented with Redis sorted sets
        to track requests and enforce rate limits across distributed workers.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum time to wait for tokens in seconds (default: 10.0)
                    None means wait indefinitely

        Returns:
            True if tokens acquired, False if timeout

        Raises:
            RateLimitException: If rate limit exceeded and no timeout
            RedisError: If Redis operation fails
        """
        start_time = time.time()

        while True:
            try:
                redis_client = await self._get_redis()

                # Use sliding window with sorted set
                current_time = time.time()
                window_start = current_time - self.window_seconds

                # Redis key for this rate limiter
                key = f"{self.key_prefix}:requests"

                # Use Redis pipeline for atomic operations
                pipe = redis_client.pipeline()

                # Remove old entries outside the window
                pipe.zremrangebyscore(key, 0, window_start)

                # Count requests in current window
                pipe.zcount(key, window_start, current_time)

                # Execute pipeline
                results = await pipe.execute()
                current_count = results[1]  # Count from zcount

                # Check if we can acquire tokens
                if current_count + tokens <= self.rate_limit:
                    # Add new request(s) to the window
                    pipe = redis_client.pipeline()
                    for i in range(tokens):
                        # Use unique timestamp for each token
                        timestamp = current_time + (i * 0.0001)
                        pipe.zadd(key, {f"{timestamp}": timestamp})

                    # Set expiry on the key (cleanup)
                    pipe.expire(key, self.window_seconds + 1)
                    await pipe.execute()

                    logger.debug(
                        f"Rate limit check passed: {current_count + tokens}/{self.rate_limit}"
                    )
                    return True

                # Rate limit exceeded
                logger.debug(
                    f"Rate limit exceeded: {current_count}/{self.rate_limit}"
                )

                # Check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(
                            f"Rate limiter timeout after {elapsed:.2f}s"
                        )
                        return False

                # Calculate wait time
                # Get oldest request in window
                oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    time_to_wait = (oldest_timestamp + self.window_seconds) - current_time
                    time_to_wait = max(0.1, min(time_to_wait, 1.0))  # Clamp between 0.1 and 1.0
                else:
                    time_to_wait = 0.1

                logger.debug(f"Waiting {time_to_wait:.2f}s for rate limit")
                await asyncio.sleep(time_to_wait)

            except RedisError as e:
                logger.error(f"Redis error in rate limiter: {str(e)}")
                # Fail open - allow the request if Redis is down
                logger.warning("Rate limiter failing open due to Redis error")
                return True

    async def get_current_usage(self) -> dict:
        """
        Get current rate limit usage statistics.

        Returns:
            Dict with usage statistics
        """
        try:
            redis_client = await self._get_redis()
            current_time = time.time()
            window_start = current_time - self.window_seconds

            key = f"{self.key_prefix}:requests"
            count = await redis_client.zcount(key, window_start, current_time)

            return {
                "current_count": count,
                "limit": self.rate_limit,
                "window_seconds": self.window_seconds,
                "percentage_used": (count / self.rate_limit) * 100,
                "available": max(0, self.rate_limit - count),
            }
        except RedisError as e:
            logger.error(f"Error getting rate limit usage: {str(e)}")
            return {
                "error": str(e),
                "current_count": 0,
                "limit": self.rate_limit,
                "window_seconds": self.window_seconds,
            }

    async def reset(self):
        """
        Reset the rate limiter (clear all tracked requests).

        Useful for testing or manual intervention.
        """
        try:
            redis_client = await self._get_redis()
            key = f"{self.key_prefix}:requests"
            await redis_client.delete(key)
            logger.info("Rate limiter reset")
        except RedisError as e:
            logger.error(f"Error resetting rate limiter: {str(e)}")


# Create singleton instance for SEC API rate limiting
sec_rate_limiter = SECRateLimiter(
    rate_limit=settings.SEC_API_RATE_LIMIT,
    window_seconds=1,
    key_prefix="sec_api",
)


def rate_limited(func):
    """
    Decorator to apply rate limiting to async functions.

    Usage:
        @rate_limited
        async def fetch_company(cik: str):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Acquire token before executing function
        acquired = await sec_rate_limiter.acquire(timeout=10.0)
        if not acquired:
            raise RateLimitException(
                f"Rate limit exceeded: {settings.SEC_API_RATE_LIMIT} requests per second"
            )

        # Execute function
        return await func(*args, **kwargs)

    return wrapper

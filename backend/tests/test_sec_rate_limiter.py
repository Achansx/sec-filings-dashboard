"""
Tests for SEC API rate limiter.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from app.services.sec_rate_limiter import (
    SECRateLimiter,
    RateLimitException,
    rate_limited,
)


@pytest.fixture
async def rate_limiter():
    """Create a test rate limiter instance."""
    limiter = SECRateLimiter(
        redis_url="redis://localhost:6379/1",  # Use test database
        rate_limit=5,  # Lower limit for faster tests
        window_seconds=1,
        key_prefix="test_ratelimit",
    )
    yield limiter
    # Cleanup
    await limiter.reset()
    await limiter.close()


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    # Set up default responses
    mock.zremrangebyscore.return_value = 0
    mock.zcount.return_value = 0
    mock.zadd.return_value = 1
    mock.expire.return_value = True
    mock.zrange.return_value = []
    mock.delete.return_value = 1
    mock.pipeline.return_value = mock
    mock.execute.return_value = [0, 0]  # [zremrangebyscore result, zcount result]
    return mock


class TestSECRateLimiter:
    """Test suite for SEC rate limiter."""

    @pytest.mark.asyncio
    async def test_initialization(self, rate_limiter):
        """Test rate limiter initialization."""
        assert rate_limiter.rate_limit == 5
        assert rate_limiter.window_seconds == 1
        assert rate_limiter.key_prefix == "test_ratelimit"

    @pytest.mark.asyncio
    async def test_acquire_single_token_success(self, rate_limiter, mock_redis):
        """Test acquiring a single token when under limit."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            result = await rate_limiter.acquire(tokens=1, timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self, rate_limiter, mock_redis):
        """Test acquiring multiple tokens at once."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            result = await rate_limiter.acquire(tokens=3, timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Test behavior when rate limit is exceeded."""
        # Mock Redis to return count at limit
        mock_redis.execute.return_value = [0, 5]  # Already at limit
        mock_redis.zrange.return_value = [(f"{time.time()}", time.time())]

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            # Should timeout since we're at limit
            result = await rate_limiter.acquire(tokens=1, timeout=0.1)
            assert result is False

    @pytest.mark.asyncio
    async def test_acquire_with_timeout(self, rate_limiter, mock_redis):
        """Test timeout behavior when rate limited."""
        # Mock rate limit exceeded
        mock_redis.execute.return_value = [0, 5]
        mock_redis.zrange.return_value = [(f"{time.time()}", time.time())]

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            start_time = time.time()
            result = await rate_limiter.acquire(tokens=1, timeout=0.5)
            elapsed = time.time() - start_time

            assert result is False
            assert elapsed >= 0.5  # Should respect timeout

    @pytest.mark.asyncio
    async def test_sliding_window_cleanup(self, rate_limiter, mock_redis):
        """Test that old requests are removed from the window."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            await rate_limiter.acquire(tokens=1, timeout=5.0)

            # Verify zremrangebyscore was called to clean old entries
            mock_redis.zremrangebyscore.assert_called()

    @pytest.mark.asyncio
    async def test_get_current_usage(self, rate_limiter, mock_redis):
        """Test getting current usage statistics."""
        mock_redis.zcount.return_value = 3

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            usage = await rate_limiter.get_current_usage()

            assert usage['current_count'] == 3
            assert usage['limit'] == 5
            assert usage['available'] == 2
            assert usage['percentage_used'] == 60.0

    @pytest.mark.asyncio
    async def test_reset(self, rate_limiter, mock_redis):
        """Test resetting the rate limiter."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            await rate_limiter.reset()
            mock_redis.delete.assert_called_with("test_ratelimit:requests")

    @pytest.mark.asyncio
    async def test_redis_error_fail_open(self, rate_limiter):
        """Test that rate limiter fails open when Redis is unavailable."""
        mock_redis = AsyncMock()
        mock_redis.pipeline.side_effect = Exception("Redis connection error")

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            # Should succeed even with Redis error (fail open)
            result = await rate_limiter.acquire(tokens=1, timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter, mock_redis):
        """Test handling concurrent requests."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            # Simulate concurrent requests
            tasks = [
                rate_limiter.acquire(tokens=1, timeout=5.0)
                for _ in range(3)
            ]
            results = await asyncio.gather(*tasks)

            # All should succeed since we're under limit
            assert all(results)

    @pytest.mark.asyncio
    async def test_rate_limited_decorator_success(self, mock_redis):
        """Test rate_limited decorator with successful request."""
        @rate_limited
        async def mock_function():
            return "success"

        # Mock the global rate limiter
        with patch('app.services.sec_rate_limiter.sec_rate_limiter') as mock_limiter:
            mock_limiter.acquire = AsyncMock(return_value=True)
            result = await mock_function()

            assert result == "success"
            mock_limiter.acquire.assert_called_once_with(timeout=10.0)

    @pytest.mark.asyncio
    async def test_rate_limited_decorator_exceeded(self):
        """Test rate_limited decorator when rate limit exceeded."""
        @rate_limited
        async def mock_function():
            return "success"

        # Mock the global rate limiter to timeout
        with patch('app.services.sec_rate_limiter.sec_rate_limiter') as mock_limiter:
            mock_limiter.acquire = AsyncMock(return_value=False)

            with pytest.raises(RateLimitException) as exc_info:
                await mock_function()

            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_distributed_rate_limiting(self, rate_limiter, mock_redis):
        """Test that rate limiting works across distributed workers."""
        # Simulate multiple workers by sharing the same Redis key
        mock_redis.execute.return_value = [0, 2]  # 2 requests already in window

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            # Should be able to add 3 more (total 5)
            result = await rate_limiter.acquire(tokens=3, timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_window_expiry(self, rate_limiter, mock_redis):
        """Test that Redis key expires after window."""
        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            await rate_limiter.acquire(tokens=1, timeout=5.0)

            # Verify expire was called with window + buffer
            mock_redis.expire.assert_called()
            call_args = mock_redis.expire.call_args
            assert call_args[0][1] == 2  # window_seconds + 1

    @pytest.mark.asyncio
    async def test_wait_calculation(self, rate_limiter, mock_redis):
        """Test that wait time is calculated correctly when rate limited."""
        current_time = time.time()
        oldest_timestamp = current_time - 0.5  # 0.5 seconds ago

        # Mock rate limit exceeded with oldest request timestamp
        mock_redis.execute.return_value = [0, 5]
        mock_redis.zrange.return_value = [(f"{oldest_timestamp}", oldest_timestamp)]

        with patch.object(rate_limiter, '_get_redis', return_value=mock_redis):
            with patch('asyncio.sleep') as mock_sleep:
                # Let it timeout quickly
                result = await rate_limiter.acquire(tokens=1, timeout=0.1)

                # Verify sleep was called with reasonable wait time
                if mock_sleep.called:
                    wait_time = mock_sleep.call_args[0][0]
                    assert 0.1 <= wait_time <= 1.0  # Clamped between 0.1 and 1.0

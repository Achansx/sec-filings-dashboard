"""
Quick validation script for SEC client setup.
Tests import and basic functionality without requiring full test environment.
"""
import asyncio
import sys

async def main():
    print("=" * 60)
    print("SEC Client Validation Script")
    print("=" * 60)

    # Test 1: Import edgartools
    print("\n[1/5] Testing edgartools import...")
    try:
        from edgar import Company, Filing, set_identity
        print("✓ edgartools imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import edgartools: {e}")
        return False

    # Test 2: Import SEC client
    print("\n[2/5] Testing SEC client import...")
    try:
        from app.services.sec_client import SECClient, sec_client
        print("✓ SEC client imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import SEC client: {e}")
        return False

    # Test 3: Import rate limiter
    print("\n[3/5] Testing rate limiter import...")
    try:
        from app.services.sec_rate_limiter import SECRateLimiter, sec_rate_limiter
        print("✓ Rate limiter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import rate limiter: {e}")
        return False

    # Test 4: Check configuration
    print("\n[4/5] Testing configuration...")
    try:
        from app.core.config import settings
        print(f"  - SEC API Rate Limit: {settings.SEC_API_RATE_LIMIT} req/s")
        print(f"  - SEC API Timeout: {settings.SEC_API_TIMEOUT}s")
        print(f"  - SEC API Max Retries: {settings.SEC_API_MAX_RETRIES}")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

    # Test 5: Basic client initialization
    print("\n[5/5] Testing SEC client initialization...")
    try:
        client = SECClient()
        print(f"  - User Agent: {client.user_agent[:50]}...")
        print("✓ SEC client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize SEC client: {e}")
        return False

    print("\n" + "=" * 60)
    print("All validations passed! ✓")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update SEC_API_USER_AGENT in .env with your name/email")
    print("2. Start Redis: docker-compose up -d redis")
    print("3. Test with real SEC API (optional):")
    print("   python -c 'from edgar import Company; print(Company(\"AAPL\").name)'")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

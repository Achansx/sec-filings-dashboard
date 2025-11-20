"""
Quick test of SEC client with real SEC API.
"""
import asyncio
from app.services.sec_client import sec_client


async def test_live_api():
    print("=" * 60)
    print("Live SEC API Integration Test")
    print("=" * 60)

    try:
        # Test 1: Get company by ticker
        print("\n[1/3] Testing company lookup by ticker (AAPL)...")
        company = await sec_client.get_company_by_ticker("AAPL")
        print(f"✓ Company: {company['name']}")
        print(f"  CIK: {company['cik']}")
        print(f"  Ticker: {company['ticker']}")
        print(f"  Industry: {company['sic_description']}")

        # Test 2: Get company by CIK
        print("\n[2/3] Testing company lookup by CIK (0000320193)...")
        company2 = await sec_client.get_company_by_cik("0000320193")
        print(f"✓ Company: {company2['name']}")
        assert company['cik'] == company2['cik']

        # Test 3: Get recent filings
        print("\n[3/3] Testing filing retrieval (10-K for AAPL)...")
        filings = await sec_client.get_filings(
            cik="0000320193",
            form_type="10-K",
            limit=3
        )
        print(f"✓ Found {len(filings)} 10-K filings")
        for filing in filings[:3]:
            print(f"  - {filing['form_type']} filed on {filing['filing_date']}")

        print("\n" + "=" * 60)
        print("All live API tests passed! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_live_api())

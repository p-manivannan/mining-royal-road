from utils.patreon_scraper import scrape_patreon

def run_tests():
    test_cases = [
        "https://www.patreon.com/wildbow",
        "https://www.patreon.com/pirateaba",
        "https://www.patreon.com/chapotraphouse"
    ]
    
    print("==================================================")
    print("         RUNNING PATREON SCRAPER TESTS            ")
    print("==================================================")
    
    for url in test_cases:
        print(f"\nTesting URL: {url}")
        try:
            result = scrape_patreon(url)
            print("Successfully scraped!")
            print(f"  Name: {result.get('name')}")
            print(f"  Subscribers Count: {result.get('subscribers')}")
            print(f"  Monthly Income: {result.get('income')} {result.get('income_currency')}")
            print(f"  Lowest Tier: {result.get('lowest_tier_title')} (${result.get('lowest_tier_price')})")
            print(f"  Highest Tier: {result.get('highest_tier_title')} (${result.get('highest_tier_price')})")
            print(f"  Number of Tiers: {result.get('number_of_tiers')}")
            
            # Assertions to ensure standard data types
            assert result.get('name') is not None, "Name should not be None"
            if result.get('subscribers') is not None:
                assert isinstance(result.get('subscribers'), int), "Subscribers must be int"
            if result.get('income') is not None:
                assert isinstance(result.get('income'), float), "Income must be float"
            if result.get('lowest_tier_price') is not None:
                assert isinstance(result.get('lowest_tier_price'), float), "Lowest tier price must be float"
            if result.get('highest_tier_price') is not None:
                assert isinstance(result.get('highest_tier_price'), float), "Highest tier price must be float"
            assert isinstance(result.get('number_of_tiers'), int), "Number of tiers must be int"
            
            print("  Status: PASSED")
        except Exception as e:
            print(f"  Status: FAILED due to error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_tests()

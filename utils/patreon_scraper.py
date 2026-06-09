import json
import re
import requests
from bs4 import BeautifulSoup

def scrape_patreon(url: str) -> dict:
    """
    Scrapes a Patreon URL and returns a dictionary of metrics including:
    - name (str): Creator name
    - subscribers (int or None): Number of subscribers (if public)
    - income (float or None): Monthly earnings (if public)
    - income_currency (str or None): Currency of earnings (e.g. 'USD')
    - lowest_tier_title (str or None): Title of lowest paid tier
    - lowest_tier_price (float or None): Price of lowest paid tier
    - highest_tier_title (str or None): Title of highest paid tier
    - highest_tier_price (float or None): Price of highest paid tier
    - number_of_tiers (int): Number of paid tiers
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    html = response.text
    
    soup = BeautifulSoup(html, "lxml")
    
    # Initialize output variables
    subscribers = None
    income = None
    income_currency = None
    lowest_tier_price = None
    lowest_tier_title = None
    highest_tier_price = None
    highest_tier_title = None
    number_of_tiers = 0
    creator_name = None
    
    # 1. Try to find Pages Router (__NEXT_DATA__)
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    campaign_data = None
    included_data = []
    
    if next_data_script and next_data_script.string:
        try:
            payload = json.loads(next_data_script.string)
            page_bootstrap = payload.get("props", {}).get("pageProps", {}).get("bootstrapEnvelope", {}).get("pageBootstrap", {})
            campaign_data = page_bootstrap.get("campaign", {})
            if isinstance(campaign_data, dict):
                included_data = campaign_data.get("included", [])
        except Exception:
            pass
            
    # 2. Try to find App Router (self.__next_f.push) if pages router didn't work or yielded no campaign
    if not campaign_data or not isinstance(campaign_data, dict) or "data" not in campaign_data:
        chunks = []
        scripts = soup.find_all("script")
        for script in scripts:
            content = script.string or ""
            for match in re.finditer(r'self\.__next_f\.push\(\s*\[\s*\d+\s*,\s*"(.*)"\s*\]\s*\)', content):
                escaped_str = match.group(1)
                try:
                    unescaped = json.loads(f'"{escaped_str}"')
                    chunks.append(unescaped)
                except Exception:
                    s = escaped_str.replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
                    chunks.append(s)
                    
        full_payload = "".join(chunks)
        if full_payload:
            idx = full_payload.find('"campaign":')
            if idx == -1:
                idx = full_payload.find('campaign":')
            if idx != -1:
                start_idx = full_payload.find("{", idx)
                if start_idx != -1:
                    try:
                        decoder = json.JSONDecoder()
                        campaign_data, _ = decoder.raw_decode(full_payload, start_idx)
                        if isinstance(campaign_data, dict):
                            included_data = campaign_data.get("included", [])
                    except Exception:
                        pass
                        
            # If included wasn't found inside the campaign block, look for it in the payload
            if not included_data:
                inc_idx = full_payload.find('"included":')
                if inc_idx != -1:
                    inc_start = full_payload.find("[", inc_idx)
                    if inc_start != -1:
                        try:
                            decoder = json.JSONDecoder()
                            included_data, _ = decoder.raw_decode(full_payload, inc_start)
                        except Exception:
                            pass

    # Process extracted campaign data
    if campaign_data and isinstance(campaign_data, dict) and "data" in campaign_data:
        attributes = campaign_data.get("data", {}).get("attributes", {})
        creator_name = attributes.get("name") or attributes.get("vanity")
        
        # Subscribers
        if attributes.get("show_patron_count", True):
            subscribers = attributes.get("patron_count")
            
        # Income
        if attributes.get("show_earnings", False) or attributes.get("pledge_sum") is not None:
            pledge_sum = attributes.get("pledge_sum") or attributes.get("campaign_pledge_sum")
            if pledge_sum is not None:
                income = float(pledge_sum) / 100.0
                income_currency = attributes.get("pledge_sum_currency") or attributes.get("currency")
                
    # Process rewards/tiers
    if included_data:
        rewards = [item for item in included_data if item.get("type") in ("reward", "tier")]
        paid_tiers = []
        for r in rewards:
            r_attrs = r.get("attributes", {})
            r_id = r.get("id")
            
            # Filter out custom/default pledge (ID "-1") and free tiers
            if r_id == "-1" or r_attrs.get("is_free_tier", False):
                continue
                
            amount_cents = r_attrs.get("amount_cents")
            if amount_cents is not None and amount_cents > 0:
                paid_tiers.append({
                    "title": r_attrs.get("title") or f"Tier {amount_cents/100:.2f}",
                    "price": float(amount_cents) / 100.0,
                    "patron_count": r_attrs.get("patron_count")
                })
                
        # Sort tiers by price
        if paid_tiers:
            paid_tiers.sort(key=lambda t: t["price"])
            number_of_tiers = len(paid_tiers)
            lowest_tier_title = paid_tiers[0]["title"]
            lowest_tier_price = paid_tiers[0]["price"]
            highest_tier_title = paid_tiers[-1]["title"]
            highest_tier_price = paid_tiers[-1]["price"]
            
            # Fallback estimation for subscribers if None
            if subscribers is None:
                total_sum = 0
                has_counts = False
                for r in rewards:
                    r_attrs = r.get("attributes", {})
                    p_count = r_attrs.get("patron_count")
                    if p_count is not None:
                        total_sum += p_count
                        has_counts = True
                if has_counts:
                    subscribers = total_sum
                    
    # Fallback to URL path parsing if creator_name couldn't be extracted
    if not creator_name:
        parts = url.rstrip("/").split("/")
        if parts:
            creator_name = parts[-1]
            
    return {
        "name": creator_name,
        "subscribers": subscribers,
        "income": income,
        "income_currency": income_currency,
        "lowest_tier_title": lowest_tier_title,
        "lowest_tier_price": lowest_tier_price,
        "highest_tier_title": highest_tier_title,
        "highest_tier_price": highest_tier_price,
        "number_of_tiers": number_of_tiers
    }

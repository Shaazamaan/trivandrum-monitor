from playwright.sync_api import sync_playwright
import time
import random

DESKTOP_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

class GoogleMapsScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Random User Agent for Stealth
        # Desktop UAs only: mobile UAs get a layout with no div[role="feed"] results list
        random_ua = random.choice(DESKTOP_USER_AGENTS)
        print(f"🕵️‍♂️ Stealth Mode: Using User-Agent: {random_ua[:30]}...")
        
        self.context = self.browser.new_context(
            user_agent=random_ua,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        self.page = self.context.new_page()

    def close_browser(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def clean_data(self, text):
        if not text: return None
        # Remove tracking params from URLs
        if "http" in text:
            return text.split("?utm")[0].split("&utm")[0]
        # Remove "Call" from phone
        return text.replace("Call", "").strip()

    def search_and_scrape(self, keyword, location="Trivandrum"):
        if not self.page:
            self.start_browser()
        
        search_query = f"{keyword} in {location}"
        print(f"Searching for: {search_query}")
        
        # RESOURCE BLOCKING (Turbo Mode)
        def route_intercept(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                route.abort()
            else:
                route.continue_()

        # RETRY LOGIC (Self-Healing)
        max_retries = 3
        search_url = f"https://www.google.com/maps/search/{search_query}"  # Store for potential reload
        
        for attempt in range(max_retries):
            try:
                self.page.route("**/*", route_intercept)
                self.page.goto(search_url, timeout=60000)
                try:
                    self.page.wait_for_selector('div[role="feed"]', timeout=10000)
                    break # Success, exit retry loop
                except:
                    if attempt == max_retries - 1:
                        print(f"No results found for {search_query} (after {max_retries} retries)")
                        return []
                    print(f"Retry {attempt+1}/{max_retries} for {search_query}...")
                    time.sleep(2)
            except Exception as e:
                print(f"Network Error on {search_query}: {e}")
                if attempt == max_retries - 1: return []
                time.sleep(5)
        
        
        try:
            # Scroll loop - do 3 scrolls for speed/efficiency per sub-location
            for _ in range(3):
                self.page.evaluate('document.querySelector("div[role=\'feed\']").scrollBy(0, 5000)')
                time.sleep(1.5)
            
            entries = self.page.query_selector_all('div[role="article"]')
            results = []
            
            for entry in entries:
                try:
                    url_el = entry.query_selector('a')
                    if not url_el: continue

                    # Google Maps now puts the business name on the link, not the article div
                    aria_label = url_el.get_attribute('aria-label') or entry.get_attribute('aria-label')
                    if not aria_label: continue
                    url = url_el.get_attribute('href')
                    url = self.clean_data(url) # Sanitize URL
                    
                    text = entry.inner_text()
                    
                    # Extract Address/Category from text
                    lines = text.split('\n')
                    category, address = "Unknown", "Trivandrum"
                    for line in lines:
                        if '·' in line:
                            parts = line.split('·')
                            if len(parts) >= 2:
                                category = parts[0].strip()
                                address = parts[1].strip()
                                break
                    
                    import re
                    # Extract Rating/Reviews
                    rating = None
                    reviews = 0
                    try:
                        rating_match = re.search(r'([0-9]\.[0-9])\s*\(([\d,]+)\)', text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                            reviews_str = rating_match.group(2).replace(',', '')
                            reviews = int(reviews_str)
                    except:
                        pass
                    
                    pid_match = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', url)
                    place_id = pid_match.group(1) if pid_match else url
                    
                    # Phone is shown in the listing text; no click-through (clicking left the list stale)
                    phone = None
                    phone_match = re.search(r'(\+?91[\s\-]?)?([6-9]\d{4}[\s\-]?\d{5}|0471[\s\-]?\d{6,7})', text)
                    if phone_match:
                        phone = phone_match.group(0).strip()
                    website = None
                    canonical_url = url

                    results.append({
                        "place_id": place_id,
                        "name": aria_label,
                        "category": category,
                        "address": address,
                        "url": canonical_url,  # Use the canonical URL from detail page
                        "rating": rating,
                        "reviews": reviews,
                        "phone": phone,
                        "website": website
                    })
                except:
                    continue
                    
            return results

        except Exception as e:
            print(f"Error scraping {search_query}: {e}")
            return []



from playwright.sync_api import sync_playwright
import time
import random
from fake_useragent import UserAgent

class GoogleMapsScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        self.ua = UserAgent()

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # Random User Agent for Stealth
        random_ua = self.ua.random
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

    def search_and_scrape(self, keyword, location="Trivandrum"):
        if not self.page:
            self.start_browser()
        
        search_query = f"{keyword} in {location}"
        print(f"Searching for: {search_query}")
        
        # RESOURCE BLOCKING (Turbo Mode)
        # We block images, fonts, and CSS to save bandwidth and speed up the scrape.
        # This makes the scraper 2x faster and less detectable (mimics "Data Saver" mode).
        def route_intercept(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                route.abort()
            else:
                route.continue_()

        try:
            self.page.route("**/*", route_intercept)
            self.page.goto(f"https://www.google.com/maps/search/{search_query}", timeout=60000)
            try:
                self.page.wait_for_selector('div[role="feed"]', timeout=5000)
            except:
                print(f"No results found for {search_query}")
                return []
            
            # Scroll loop - do 3 scrolls for speed/efficiency per sub-location
            for _ in range(3):
                self.page.evaluate('document.querySelector("div[role=\'feed\']").scrollBy(0, 5000)')
                time.sleep(1.5)
            
            entries = self.page.query_selector_all('div[role="article"]')
            results = []
            
            for entry in entries:
                try:
                    aria_label = entry.get_attribute('aria-label')
                    if not aria_label: continue
                        
                    url_el = entry.query_selector('a')
                    if not url_el: continue
                    url = url_el.get_attribute('href')
                    
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
                    # Format is often "4.7(105)" or similar in the text
                    rating = None
                    reviews = 0
                    try:
                        # Search for pattern like 4.7(1,234)
                        # We look for a float followed by parens with digits
                        rating_match = re.search(r'([0-9]\.[0-9])\s*\(([\d,]+)\)', text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                            reviews_str = rating_match.group(2).replace(',', '')
                            reviews = int(reviews_str)
                    except:
                        pass # Keep defaults

                    pid_match = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', url)
                    place_id = pid_match.group(1) if pid_match else url
                    
                    
                    # Extract Phone and Website from buttons
                    phone = None
                    website = None
                    
                    # 1. Try to find Phone in "Call" button aria-label
                    try:
                        # Look for button/link with aria-label starting with "Call"
                        # E.g. aria-label="Call +91 1234567890"
                        phone_el = entry.query_selector('[aria-label^="Call"]')
                        if phone_el:
                            lbl = phone_el.get_attribute('aria-label')
                            if lbl:
                                # Remove "Call " prefix
                                phone = lbl.replace("Call", "").strip()
                    except:
                        pass

                    # 2. Try to find Website link
                    try:
                        # Often has data-value="Website" or aria-label="Website"
                        # Or simply is an 'a' tag that is NOT the main map link
                        website_el = entry.query_selector('a[data-value="Website"]')
                        if not website_el:
                            website_el = entry.query_selector('a[aria-label="Website"]')
                        
                        if website_el:
                            website = website_el.get_attribute('href')
                            # Clean up Google redirect if present
                            if "google.com/url" in website:
                                import urllib.parse
                                parsed = urllib.parse.urlparse(website)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if 'q' in qs:
                                    website = qs['q'][0]
                    except:
                        pass
                    
                    results.append({
                        "place_id": place_id,
                        "name": aria_label,
                        "category": category,
                        "address": address,
                        "url": url,
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



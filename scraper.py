from playwright.sync_api import sync_playwright
import time
import random

class GoogleMapsScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.page = self.context.new_page()

    def close_browser(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search_and_scrape(self, keyword, location="Trivandrum"):
        """
        Searches for a keyword in a location and returns a list of businesses.
        """
        if not self.page:
            self.start_browser()
        
        search_query = f"{keyword} in {location}"
        print(f"Searching for: {search_query}")
        
        try:
            self.page.goto(f"https://www.google.com/maps/search/{search_query}")
            self.page.wait_for_selector('div[role="feed"]', timeout=10000)
            
            # Scroll to load more results
            # We will scroll a few times to get a decent batch. 
            # For "monitoring" we might not need to scroll *everything* every time if we run frequently.
            # But initial run might need deep scroll.
            
            scrollable_div = 'div[role="feed"]'
            
            # Scroll loop - let's do 5 scrolls for now to keep it fast for testing
            for _ in range(5):
                # Using more robust evaluate
                self.page.evaluate('document.querySelector("div[role=\'feed\']").scrollBy(0, 5000)')
                time.sleep(2)
            
            # Process results
            entries = self.page.query_selector_all('div[role="article"]')
            results = []
            
            for entry in entries:
                try:
                    aria_label = entry.get_attribute('aria-label')
                    if not aria_label:
                        continue
                        
                    # Extract link to get Place ID (cid) or coordinate data
                    link_el = entry.query_selector('a[href*="/maps/place/"]')
                    if not link_el:
                         continue
                         
                    url = link_el.get_attribute('href')
                    
                    # Basic parsing
                    # Place ID is tricky to extract perfectly without clicking, 
                    # but the URL often contains coordinates or a unique hex string.
                    # We will use the URL itself or a hash of the name+address as a fallback ID if needed.
                    # Actually, the most reliable "ID" in this context without waiting for full load 
                    # is often just the clean URL or Name.
                    
                    # Splitting text content for details
                    text_content = entry.inner_text().split('\n')
                    
                    # Simple heuristic for details
                    # [Name, Rating, Category, Address, Status/OpenTime]
                    name = aria_label
                    category = "Unknown"
                    address = "Trivandrum" # Default if not found
                    phone = None
                    website = None
                    
                    # Try to find category and address in text
                    # This is brittle as GMaps changes DOM often. 
                    # Usually: 
                    # Line 1: Rating (4.5) ...
                    # Line 2: Category · Address
                    
                    # Refinement:
                    # Let's iterate text lines to find the one with interpunct '·'
                    for line in text_content:
                        if '·' in line:
                            parts = line.split('·')
                            if len(parts) >= 2:
                                category = parts[0].strip()
                                address = parts[1].strip()
                                break
                    
                    # We really want a unique ID. 
                    # URL usually looks like: https://www.google.com/maps/place/Business+Name/data=...!1s0x...!3m1...
                    # The '1s0x...' part is a feature ID.
                    import re
                    place_id_match = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', url)
                    place_id = place_id_match.group(1) if place_id_match else url
                    
                    business = {
                        "place_id": place_id,
                        "name": name,
                        "category": category,
                        "address": address,
                        "phone": phone, # Hard to get without clicking
                        "website": website, # Hard to get without clicking
                        "url": url
                    }
                    results.append(business)
                    
                except Exception as e:
                    print(f"Error parsing entry: {e}")
                    continue
                    
            return results

        except Exception as e:
            print(f"Error during scrape: {e}")
            return []

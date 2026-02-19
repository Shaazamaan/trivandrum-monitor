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
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
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
                    aria_label = entry.get_attribute('aria-label')
                    if not aria_label: continue
                        
                    url_el = entry.query_selector('a')
                    if not url_el: continue
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
                    
                    # Extract Phone and Website by clicking into detail page
                    phone = None
                    website = None
                    canonical_url = url  # Fallback to search result URL
                    
                    try:
                        # Click the listing to open detail panel
                        url_el.click()
                        
                        # Wait for detail panel to load (dynamic wait up to 5 seconds)
                        try:
                            self.page.wait_for_selector('div[role="main"]', timeout=5000)
                        except:
                            # Detail panel didn't load, skip this listing
                            print(f"⚠️ Detail panel timeout for: {aria_label[:30]}...")
                            raise Exception("Detail panel load timeout")
                        
                        # Get the canonical Place URL from browser address bar
                        current_url = self.page.url
                        if '/maps/place/' in current_url:
                            canonical_url = current_url
                        else:
                            print(f"⚠️ URL didn't navigate to place page: {current_url[:50]}")
                        
                        # Extract phone from detail panel
                        # Extract phone from detail panel
                        # Strategy 1: Look for phone number button (specific data-item-id)
                        try:
                            phone_button = self.page.query_selector('button[data-item-id^="phone"]')
                            if phone_button:
                                phone_text = phone_button.get_attribute('aria-label')
                                if phone_text:
                                    phone_match = re.search(r'[\d\s\+\-\(\)]+$', phone_text)
                                    if phone_match:
                                        phone = phone_match.group(0).strip()
                        except: pass

                        # Strategy 2: Look for any button with a phone icon or "Call" text
                        if not phone:
                            try:
                                buttons = self.page.query_selector_all('button')
                                for btn in buttons:
                                    txt = btn.inner_text()
                                    if '0471' in txt or '+91' in txt or (len(re.findall(r'\d', txt)) > 6 and 'Call' not in txt): # Primitive phone check
                                         phone_match = re.search(r'(\+91[\s\-]?)?[6-9]\d{9}|0471[\s\-]?\d+', txt)
                                         if phone_match:
                                             phone = phone_match.group(0).strip()
                                             break
                                    # Check aria-label of all buttons
                                    lbl = btn.get_attribute('aria-label')
                                    if lbl and ('Phone:' in lbl or 'Call' in lbl):
                                         phone_match = re.search(r'[\d\s\+\-\(\)]+$', lbl)
                                         if phone_match:
                                             phone = phone_match.group(0).strip()
                                             break
                            except: pass

                        # Strategy 3: Look in the detail panel text (broad regex)
                        if not phone:
                            detail_panel = self.page.query_selector('div[role="main"]')
                            if detail_panel:
                                detail_text = detail_panel.inner_text()
                                # Match Indian phone patterns (Mobile & Landline)
                                phone_match = re.search(r'(\+?91[\s\-]?)?([6-9]\d{9}|0471[\s\-]?\d{6,7})', detail_text)
                                if phone_match:
                                    phone = phone_match.group(0).strip()
                        
                        print(f"   -> Extracted Phone: {phone}, URL: {canonical_url[:40]}...")
                        
                        # Extract website
                        website_link = self.page.query_selector('a[data-item-id="authority"]')
                        if not website_link:
                            website_link = self.page.query_selector('a[aria-label*="Website"]')
                        
                        if website_link:
                            website = website_link.get_attribute('href')
                            if website and "google.com/url" in website:
                                import urllib.parse
                                parsed = urllib.parse.urlparse(website)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if 'q' in qs:
                                    website = qs['q'][0]
                            if website:
                                website = self.clean_data(website)
                        
                        # Go back to results list with error handling
                        try:
                            self.page.go_back()
                            # Wait for results feed to be visible again
                            self.page.wait_for_selector('div[role="feed"]', timeout=3000)
                        except:
                            # Fallback: reload the search if go_back fails
                            print(f"⚠️ go_back() failed, reloading search...")
                            self.page.goto(search_url)
                            self.page.wait_for_selector('div[role="feed"]', timeout=10000)
                        
                    except Exception as e:
                        print(f"❌ Error extracting details for {aria_label}: {e}")
                        # Try to recover: reload the search page
                        try:
                            self.page.goto(search_url)
                            self.page.wait_for_selector('div[role="feed"]', timeout=10000)
                        except:
                            pass  # Continue with None values
                    
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



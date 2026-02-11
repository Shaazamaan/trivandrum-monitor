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
        if not self.page:
            self.start_browser()
        
        search_query = f"{keyword} in {location}"
        print(f"Searching for: {search_query}")
        
        try:
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
                    
                    results.append({
                        "place_id": place_id,
                        "name": aria_label,
                        "category": category,
                        "address": address,
                        "url": url,
                        "rating": rating,
                        "reviews": reviews,
                        "phone": None,
                        "website": None
                    })
                except:
                    continue
                    
            return results

        except Exception as e:
            print(f"Error scraping {search_query}: {e}")
            return []

TRIVANDRUM_LOCATIONS = [
    "Thiruvananthapuram", "Andoorkonam", "Attipra", "Cheruvakkal", "Ayiroopara", "Kadakampally", "Kadinamkulam", "Kalliyoor", 
    "Kazhakoottam", "Keezhthonnakkal", "Kowdiar", "Kudappanakunnu", "Manacaud", "Melthonackal", "Muttathara", "Nemom", "Pallipuram", 
    "Pangapara", "Pattom", "Peroorkada", "Pettah", "Sasthamangalam", "Thirumala", "Thiruvallam", "Thycaud", "Uliyazhathura", "Uloor", 
    "Vanchiyoor", "Vattiyoorkavu", "Veiloor", "Veganoor", "Menamkulam", "Alamcode", "Attingal", "Azhoor", "Edakode", "Koonthalloor", 
    "Kadakkavur", "Karavaram", "Keezhattingal", "Kizhuvillam", "Kilimanoor", "Koduvazhanoor", "Nagaroor", "Pazhayakunnummel", "Pulimath", 
    "Sarkara", "Vakkam", "Vellalloor", "Avanavancherry", "Elamba", "Mudhakkal", "Anchuthengu", "Anad", "Aruvikkara", "Aryanad", 
    "Kallara Nedumangad", "Karakulam", "Karippur", "Koliyacode", "Kurupuzha", "Manikkal", "Nedumangad", "Nellanad", "Palode", "Panavoor", 
    "Peringammala", "Pullampara", "Thekkada", "Thennoor", "Tholicode", "Uzhamalakkal", "Vamanapuram", "Vattappara", "Vellanad", 
    "Vembayam", "Vithura", "Pangode", "Anavoor", "Athiyannoor", "Chenkal", "Kanjiramkulam", "Karumkulam", "Karode", "Kollayil", 
    "Kottukal", "Kulathoor", "Kunnathukal", "Neyyattinkara", "Pallichal", "Parassala", "Parasuvaikkal", "Perumkadavila", "Perumpazhuthoor", 
    "Thirupuram", "Vellarada", "Vizhinjam", "Balaramapuram", "Poovar", "Amboori", "Kallikkad", "Keezharoor", "Kulathummal", "Malayinkeezh", 
    "Mannoorkkara", "Maranallur", "Ottasekharamangalam", "Perumkulam", "Vazhichal", "Veeranakav", "Vilappil", "Vilavoorkal", "Ayiroor", 
    "Chemmaruthi", "Cherunniyur", "Edava", "Kudavoor", "Madavoor", "Manamboor", "Navaikulam", "Ottur", "Pallikkal", "Varkala", "Vettur", 
    "Chirayinkeezh", "Kattakada"
]

import urllib.parse
from scraper import GoogleMapsScraper
from database import Storage
from notifier import DiscordNotifier
from socials import InstagramFinder
import time
import random

# CONFIG
WEBHOOK_URL = "https://discord.com/api/webhooks/1470815883613176003/zlIN-_hKPMPGYIvmyK3jWhPrjrWNQlXUpBLBCr7JuK3HxJ4WB26-5fwt84Nv-hJCesHV"
KEYWORDS = [
    "gym", "clinic", "restaurant", "cafe", "boutique", 
    "salon", "supermarket", "bakery", "hotel"
]
LOCATION = "Trivandrum"

def main():
    print("Starting Google Maps Monitor (Cloud Mode)...")
    
    # Initialize components
    storage = Storage()
    notifier = DiscordNotifier(WEBHOOK_URL)
    
    # Check if this is the first run (DB is empty)
    # We'll check by querying the count
    is_first_run = storage.get_count() == 0
    if is_first_run:
        print("First run detected! Monitoring mode: POPULATION (No alerts will be sent).")
    else:
        print("Monitoring mode: ACTIVE (Alerts enabled).")

    scraper = GoogleMapsScraper(headless=True) # Always headless for cloud
    scraper.start_browser()
    
    try:
        # Single Pass Loop (for Cron)
        for keyword in KEYWORDS:
            print(f"Checking for new '{keyword}' in {LOCATION}...")
            
            results = scraper.search_and_scrape(keyword, LOCATION)
            print(f"Found {len(results)} results for {keyword}.")
            
            new_count = 0
            for business in results:
                if storage.is_new(business['place_id']):
                    # Save first
                    storage.add_place(business)
                    new_count += 1
                    
                    # Only alert if NOT first run
                    if not is_first_run:
                        print(f"NEW FOUND: {business['name']} - Sending Alert")
                        
                        # Generate a smart search link for Instagram
                        # We do this instead of scraping to prevent the free cloud IP from being blocked by Google.
                        query = f"{business['name']} trivandrum instagram"
                        ig_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                        
                        notifier.send_alert(business, ig_url)
                        time.sleep(1) # Rate limit protection
                    else:
                        print(f"Discovered existing: {business['name']} (Silent Save)")

            print(f"Processed keyword '{keyword}'. New/Added: {new_count}")
            # Short delay between keywords
            time.sleep(random.randint(2, 5))
            
        # Export API Data
        storage.export_to_json("data.json")
        
        # Export Metadata (Last Run Time)
        import json
        from datetime import datetime
        with open("metadata.json", "w") as f:
            json.dump({"last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f)
            
    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        scraper.close_browser()
        print("Run complete.")

if __name__ == "__main__":
    main()

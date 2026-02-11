import urllib.parse
from scraper import GoogleMapsScraper, TRIVANDRUM_LOCATIONS
from database import Storage
from notifier import DiscordNotifier
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
    is_first_run = storage.get_count() == 0
    if is_first_run:
        print("First run detected! Monitoring mode: POPULATION (No alerts will be sent).")
    else:
        print("Monitoring mode: ACTIVE (Alerts enabled).")

    scraper = GoogleMapsScraper(headless=True)
    scraper.start_browser()
    
    try:
        all_results = []
        
        # 1. Base Scan: "Keyword + Trivandrum" (General Coverage)
        print("--- Starting Base Scan (Trivandrum) ---")
        for keyword in KEYWORDS:
            print(f"Scanning {keyword} in Trivandrum...")
            results = scraper.search_and_scrape(keyword, "Trivandrum")
            all_results.extend(results)
            time.sleep(2)

        # 2. Deep Scan: Pick 2 Random Locations from the expanded list
        random_locations = random.sample(TRIVANDRUM_LOCATIONS, 2)
        print(f"--- Starting Deep Scan ({', '.join(random_locations)}) ---")
        
        for loc in random_locations:
            for keyword in KEYWORDS:
                print(f"Scanning {keyword} in {loc}...")
                results = scraper.search_and_scrape(keyword, loc)
                all_results.extend(results)
                time.sleep(2)
        
        # Process All Results
        new_count = 0
        for business in all_results:
            if storage.is_new(business['place_id']):
                # Save first
                storage.add_place(business)
                new_count += 1
                
                if not is_first_run:
                    print(f"NEW FOUND: {business['name']} - Sending Alert")
                    query = f"{business['name']} trivandrum instagram"
                    ig_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                    notifier.send_alert(business, ig_url)
                    time.sleep(1)
        
        print(f"Run complete. Total New: {new_count}")

        # Export API Data
        storage.export_to_json("data.json")
        
        # Export Metadata
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

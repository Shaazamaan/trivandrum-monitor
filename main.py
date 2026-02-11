import urllib.parse
from scraper import GoogleMapsScraper, TRIVANDRUM_LOCATIONS
from database import Storage
from notifier import DiscordNotifier
import time
import random

# CONFIG
WEBHOOK_URL = "https://discord.com/api/webhooks/1470815883613176003/zlIN-_hKPMPGYIvmyK3jWhPrjrWNQlXUpBLBCr7JuK3HxJ4WB26-5fwt84Nv-hJCesHV"

# Import Advanced Taxonomy
from keywords import ALL_KEYWORDS

# CONFIG
# Set to True for the first 48h to populate the DB without spamming alerts.
# After 2 days, set this to False to start receiving "New Business" notifications.
SILENT_MODE = True 

# Dynamic Keyword Selection
# We pick 10 random High-Value keywords per run to keep it fresh and broad.
# This ensures we cycle through "Orthodontist", "Patent Attorney", "Vegan Restaurant" etc over time.
TARGET_KEYWORDS = random.sample(ALL_KEYWORDS, 10)

LOCATION = "Trivandrum"

def main():
    print("Starting Google Maps Monitor (Cloud Mode)...")
    
    # Initialize components
    storage = Storage()
    notifier = DiscordNotifier(WEBHOOK_URL)
    
    # Check if this is the first run (DB is empty)
    is_first_run = storage.get_count() == 0
    
    if SILENT_MODE:
        print("CONFIG: SILENT_MODE is ON. Populating database without alerts...")
    elif is_first_run:
        print("First run detected! Monitoring mode: POPULATION (No alerts will be sent).")
    else:
        print("Monitoring mode: ACTIVE (Alerts enabled).")

    scraper = GoogleMapsScraper(headless=True)
    scraper.start_browser()
    
    try:
        all_results = []
        
        # 1. Base Scan: "Keyword + Trivandrum" (General Coverage)
        print("--- Starting Base Scan (Trivandrum) ---")
        for keyword in TARGET_KEYWORDS:
            print(f"Scanning {keyword} in Trivandrum...")
            results = scraper.search_and_scrape(keyword, "Trivandrum")
            all_results.extend(results)
            time.sleep(2)

        # 2. Deep Scan: Pick 4 Random Locations from the expanded list
        # We have ~85 locations. 
        # 4 locs * 72 runs/day = 288 scans/day.
        # Probability of a location being missed in 24h drops to < 2%.
        random_locations = random.sample(TRIVANDRUM_LOCATIONS, 4)
        print(f"--- Starting Deep Scan ({', '.join(random_locations)}) ---")
        
        for loc in random_locations:
            for keyword in TARGET_KEYWORDS:
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
                
                if not is_first_run and not SILENT_MODE:
                    # Intelligence Filter: High Priority if Reviews < 5
                    is_fresh = business.get('reviews', 0) < 5
                    fresh_tag = " [💎 FRESH OPPORTUNITY]" if is_fresh else ""
                    
                    print(f"NEW FOUND: {business['name']} ({business.get('reviews', 0)} reviews){fresh_tag} - Sending Alert")
                    query = f"{business['name']} trivandrum instagram"
                    ig_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                    
                    # Append tag to alert title if possible, or just log it
                    # We pass the modified business object or handled in notifier?
                    # For now just send as is, but we log the 'Freshness'.
                    business['is_fresh'] = is_fresh
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

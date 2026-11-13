from scraper import GoogleMapsScraper
from database import Storage
from notifier import DiscordNotifier
import time
import random
import urllib.parse

# CONFIG
import os
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Import Advanced Taxonomy
from keywords import ALL_KEYWORDS

# CONFIG
# Set to True for the first 48h to populate the DB without spamming alerts.
# After 2 days, set this to False to start receiving "New Business" notifications.
SILENT_MODE = False 

# Locations to Scan
TRIVANDRUM_LOCATIONS = [
    "Kazhakoottam", "Technopark", "Thampanoor", "Pattom", "Kowdiar", "Vazhuthacaud", "Palayam",
    "East Fort", "Ulloor", "Kesavadasapuram", "Sreekaryam", "Varkala", "Attingal", "Neyyattinkara",
    "Nedumangad", "Vizhinjam", "Poovar", "Kattakada", "Parassala", "Pothencode", "Vattiyoorkavu",
    "Peroorkada", "Nemom", "Manacaud", "Kadinamkulam", "Chirayinkeezh", "Kilimanoor",
    "Venjaramoodu", "Vithura", "Ponmudi", "Kallambalam"
]

# Dynamic Keyword Selection
# REDUCED BATCH SIZE FOR SAFETY
# We pick 3 random High-Value keywords per run to keep runtime short (~3-5 mins).
# 3 keywords * 3 locations = 9 searches per run.
# This prevents GitHub Actions timeouts and Google IP blocks.
TARGET_KEYWORDS = random.sample(ALL_KEYWORDS, 3)

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

        # 2. Deep Scan: Pick Random Locations
        # We process fewer locations per run but run often (every 20 mins).
        # This keeps the total daily coverage high while preventing crashes.
        random_locations = random.sample(TRIVANDRUM_LOCATIONS, 3)
        print(f"--- Starting Deep Scan ({', '.join(random_locations)}) ---")
        
        for loc in random_locations:
            for keyword in TARGET_KEYWORDS:
                print(f"Scanning {keyword} in {loc}...")
                results = scraper.search_and_scrape(keyword, loc)
                all_results.extend(results)
                time.sleep(2)
        
        # Process All Results
        new_count = 0
        fresh_count = 0
        for business in all_results:
            if storage.is_new(business['place_id']):
                # Save first
                storage.add_place(business)
                new_count += 1
                
                # FRESH LEAD = not seen before AND no rating/reviews yet on Google Maps.
                # Google doesn't publish a listing date; a listing with zero reviews
                # is the strongest signal that it was just added. Older businesses we
                # simply hadn't scanned before are saved silently, never alerted.
                is_fresh = business.get('rating') is None and business.get('reviews', 0) == 0
                if is_fresh and not is_first_run and not SILENT_MODE and WEBHOOK_URL:
                    fresh_count += 1
                    print(f"FRESH LEAD: {business['name']} - Sending Alert")
                    query = f"{business['name']} trivandrum instagram"
                    ig_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                    business['is_fresh'] = True
                    notifier.send_alert(business, ig_url)
                    time.sleep(1)

        print(f"Fresh leads alerted: {fresh_count}")
        print(f"Run complete. Total New: {new_count}")

        # Export API Data (Hot & Cold)
        storage.export_partitioned()
        
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

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
KEYWORDS_PER_RUN = 36  # ~8 min per run; 824 keywords / 36 = ~23 runs = each search re-checked about every 8 hours

LOCATION = "Trivandrum"

def tag_results(storage, results, keyword, location):
    # First time this search runs: its results become the snapshot (no alerts).
    # Later runs of the same search: anything not in the snapshot is NEW.
    baselined = storage.is_baselined(keyword, location)
    for r in results:
        r['_baselined'] = baselined
    if results:
        storage.mark_baselined(keyword, location)
    print(f"   {'compare' if baselined else 'snapshot'}: {keyword} @ {location} ({len(results)} results)")

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
        
        # Fixed rotation (not random) so every search repeats on a predictable cycle:
        # first pass = snapshot, every later pass = compare against snapshot.
        offset = storage.get_state('keyword_offset', 0) % len(ALL_KEYWORDS)
        batch = [ALL_KEYWORDS[(offset + i) % len(ALL_KEYWORDS)] for i in range(KEYWORDS_PER_RUN)]
        print(f"--- Rotation scan: keywords {offset}..{offset + KEYWORDS_PER_RUN - 1} of {len(ALL_KEYWORDS)} ---")
        for keyword in batch:
            results = scraper.search_and_scrape(keyword, LOCATION)
            tag_results(storage, results, keyword, LOCATION)
            all_results.extend(results)
            time.sleep(2)
        storage.set_state('keyword_offset', (offset + KEYWORDS_PER_RUN) % len(ALL_KEYWORDS))

        # Process All Results
        new_count = 0
        fresh_count = 0
        for business in all_results:
            if storage.is_new(business['place_id']):
                # Save first
                storage.add_place(business)
                new_count += 1
                
                # NEW LEAD = not in DB, found by a search that already had a snapshot.
                is_new_lead = business.get('_baselined', False)
                is_fresh = is_new_lead
                if is_fresh and not is_first_run and not SILENT_MODE and WEBHOOK_URL:
                    fresh_count += 1
                    print(f"NEW LEAD: {business['name']} ({business.get('reviews', 0)} reviews) - Sending Alert")
                    query = f"{business['name']} trivandrum instagram"
                    ig_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                    business['is_fresh'] = business.get('reviews', 0) == 0
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

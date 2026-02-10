from playwright.sync_api import sync_playwright
import time
import random

class InstagramFinder:
    def __init__(self):
        pass

    def find_instagram(self, business_name, location="Trivandrum"):
        """
        Performs a Google Search to find a matching Instagram profile.
        Returns the URL if found, else None.
        """
        query = f'site:instagram.com "{business_name}" {location}'
        url = None
        
        # We will use a separate playwright instance or the existing one depending on how main loop is structured.
        # For simplicity, this function can launch its own short-lived context or accept a page.
        # To avoid blocking, we'll assume this is called with a fresh context for now, 
        # but in production we should reuse the browser.
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f"https://www.google.com/search?q={query}")
                
                # Wait for results
                page.wait_for_selector('div.g', timeout=5000)
                
                # Get first result
                first_result = page.query_selector('div.g a')
                if first_result:
                    url = first_result.get_attribute('href')
                    if "instagram.com" not in url:
                        url = None
                
                browser.close()
        except Exception as e:
            print(f"Error finding Instagram: {e}")
            
        return url

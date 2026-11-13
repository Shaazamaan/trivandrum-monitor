import requests
import json
import time
from datetime import datetime

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_alert(self, business, instagram_url=None):
        """
        Sends a rich embed to Discord.
        business: dict containing business details
        instagram_url: optional string URL
        """
        
        embed = {
            "title": f"🆕 New Listing: {business.get('name')}",
            "url": business.get('url') or None,
            "color": 5814783,  # Greenish
            "fields": [
                {
                    "name": "Category",
                    "value": business.get('category') or 'N/A',
                    "inline": True
                },
                {
                    "name": "Phone",
                    "value": business.get('phone') or 'N/A',
                    "inline": True
                },
                {
                    "name": "Address",
                    "value": business.get('address') or 'N/A',
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Discovered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }

        if business.get('url'):
            embed["fields"].append({
                "name": "Google Maps",
                "value": f"[Open on Google Maps]({business.get('url')})",
                "inline": False
            })

        if business.get('website'):
             embed["fields"].append({
                "name": "Website",
                "value": business.get('website'),
                "inline": False
            })
             
        # Add a direct search link for Instagram
        if instagram_url:
            embed["fields"].append({
                "name": "Socials",
                "value": f"[Find on Instagram]({instagram_url})",
                "inline": False
            })

        payload = {
            "embeds": [embed]
        }

        # Discord rate-limits webhooks (~5 requests / 2s). On 429, wait the
        # requested time and retry instead of dropping the alert.
        for attempt in range(5):
            try:
                response = requests.post(
                    self.webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                if response.status_code == 429:
                    wait = float(response.json().get("retry_after", 2))
                    time.sleep(wait + 0.5)
                    continue
                response.raise_for_status()
                return
            except Exception as e:
                print(f"Failed to send Discord alert: {type(e).__name__} {getattr(getattr(e, 'response', None), 'status_code', '')}")
                return
        print("Failed to send Discord alert: still rate limited after 5 attempts")

import requests
import json
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
            "title": f"New Business Detected: {business.get('name')}",
            "color": 5814783,  # Greenish
            "fields": [
                {
                    "name": "Category",
                    "value": business.get('category', 'N/A'),
                    "inline": True
                },
                {
                    "name": "Phone",
                    "value": business.get('phone', 'N/A'),
                    "inline": True
                },
                {
                    "name": "Address",
                    "value": business.get('address', 'N/A'),
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Discovered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }

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

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")

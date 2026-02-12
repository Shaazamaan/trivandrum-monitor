# HASHCOVETS Monitor 🦅

> **Live Intelligence Dashboard for Trivandrum Business Ecosystem.**

![HASHCOVETS Monitor](logo-full.png)

## Overview
HASHCOVETS Monitor is a serverless, self-healing intelligence system designed to track new business openings, trends, and commercial activities in Trivandrum, Kerala. It operates on a zero-cost architecture using **GitHub Actions** for scraping and **GitHub Pages** for hosting.

## Features
*   **🕵️‍♂️ Stealth Scraper:** Python/Playwright-based engine with User-Agent rotation and resource blocking (Turbo Mode).
*   **✨ Self-Healing:** Automatic retry logic and data sanitization for resilience against network flakes.
*   **📊 Live Dashboard:** A static HTML5/JS dashboard that requires zero backend, reading directly from `data.json`.
*   **📱 PWA Ready:** Installable on iOS/Android with offline support and branding.
*   **⚡ Zero-Cost:** 100% Free to run (Uses Github Actions Free Tier).

## Architecture
1.  **Scraper (`scraper.py`)**: Runs daily via GitHub Actions.
2.  **Orchestrator (`monitor.yml`)**: Manages the schedule (every 6 hours) and caches dependencies (`pip`, `playwright`) for speed.
3.  **Frontend (`index.html`)**: Visualizes the data with Charts, Maps (Leaflet), and Smart "Vibe Analysis".

## Deployment
This system is deployed automatically.
*   **Live URL:** [https://shaazamaan.github.io/trivandrum-monitor/](https://shaazamaan.github.io/trivandrum-monitor/)
*   **Schedule:** Runs automatically at 00:00, 06:00, 12:00, 18:00 UTC.

## Local Development
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run scraper manually
python scraper.py
```

## Credits
Built for **Hashcovets**.
*Engineered by Antigravity.*

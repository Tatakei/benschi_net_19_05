import os
import json
import time
import requests

# Base URL for the Hypixel SkyBlock Auctions API
BASE_URL = "https://api.hypixel.net/v2/skyblock/auctions"

# CHANGED: Removed the leading slash so it saves inside your current project folder
SAVE_DIR = "static/files/json/hypixel/auctions"

# ADDED: Standard browser headers to slip past Cloudflare bot protection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def fetch_and_save_auction_pages():
    # Automatically create the folder structure relative to where the script is run
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        print(f"Created directory structure: {os.path.abspath(SAVE_DIR)}")

    print("Fetching page 0 to determine total pages...")

    try:
        # Request page 0 using our browser headers
        response = requests.get(f"{BASE_URL}?page=0", headers=HEADERS)

        # Let's print out what actually happened if it fails
        if response.status_code != 200:
            print(f"API Error! Received HTTP Code: {response.status_code}")
            print("This usually means Cloudflare blocked the script or the API is down.")
            return

        data = response.json()

        if "totalPages" in data:
            total_pages = data["totalPages"]
            print(f"Success! Total pages to fetch: {total_pages}\n")
        else:
            print("Error: Could not find 'totalPages' in the JSON keys.")
            print(f"Available root keys are: {list(data.keys())}")
            return

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching page 0: {e}")
        return

    # Loop through all pages from 0 to total_pages - 1
    for page in range(total_pages):
        print(f"Fetching page {page} of {total_pages - 1}...")

        try:
            page_response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS)
            page_response.raise_for_status()
            page_data = page_response.json()

            # Construct the filename cleanly using os.path
            file_name = f"data_{page}.json"
            file_path = os.path.join(SAVE_DIR, file_name)

            # Save the JSON data to the file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)

            print(f"-> Saved page {page} to: {file_path}")

        except requests.exceptions.RequestException as e:
            print(f"-> Failed to download page {page}: {e}")
        except IOError as e:
            print(f"-> File system error saving page {page}: {e}")

        # Enforce the 5-second delay between requests
        if page < total_pages - 1:
            print("Waiting 5 seconds before the next request...\n")
            time.sleep(5)

    print("\nFinished downloading all pages!")

if __name__ == "__main__":
    fetch_and_save_auction_pages()
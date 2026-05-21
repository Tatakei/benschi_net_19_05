import requests.exceptions
import os
from dotenv import load_dotenv
import yaml

load_dotenv()

class Hypixel:
    class Auction:
        class Scraper:
            @staticmethod
            def fetch_and_save_auction_pages():
                BASE_URL = os.environ.get('HYPIXEL__API__AUCTIONS__URL')

                SAVE_DIR = os.environ.get('HYPIXEL__API__AUCTIONS__FILE_PATH')

                HEADERS = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                }

                if not os.path.exists(SAVE_DIR):
                    os.makedirs(SAVE_DIR)
                    print(f"Created directory Structure: {os.path.abspath(SAVE_DIR)}")

                print("Fetching page 0 to determine total pages...")

                try:
                    response = requests.get(f"{BASE_URL}?page=0", headers=HEADERS)

                    if response.status_code != 200:
                        print(f"API Error! Received HTTP Code: {response.status_code}")
                        print("Either Cloudflare blocked you or API is down.")
                        return

                    data = response.json()

                    if "totalPages" in data:
                        total_pages = data["totalPages"]
                        print(f"Success! Total Pages to fetch: {total_pages}\n")
                    else:
                        print("Error: Could not find 'totalPages' in the JSON Keys.")
                        print(f"Available root keys are: {list(data.keys())}")

                except requests.exceptions.RequestException as e:
                    print(f"An error occurred while fetching page 0: {e}")
                    return

                for page in range(total_pages):
                    print(f"Fetching Page {page} of {total_pages - 1}...")

                    try:
                        page_response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS)
                        page_response.raise_for_status()
                        page_data = page_response.json()

                        file_name = f"data_{page}.json"
                        file_path = os.path.join(SAVE_DIR, file_name)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(page_data, f, ensure_ascii=False, indent=4)

                        print(f"-> Saved Page {page} to: {file_path}")

                    except requests.exceptions.RequestException as e:
                        print(f"-> Failed to download page {page}: {e}")
                    except IOError as e:
                        print(f"-> File System error saving page {page}: {e}")

                    if page < total_pages - 1:
                        print("Waiting 2 seconds before the next request...\n")
                        time.sleep(2)

    class Item:
        _registry = {}

        @classmethod
        def load_registry(cls, yaml_file):
            with open(yaml_file, 'r') as file:
                cls._registry = yaml.safe_load(file) or {}

        @classmethod
        def fetch(cls, item_id):
            return cls._registry.get(item_id)

        @classmethod
        def get_all(cls):
            return cls._registry

    class Forge:
        @staticmethod
        def get_total_ingredients(item_id, multiplier=1):
            item_data = Hypixel.Item.fetch(item_id)
            if not item_data or not item_data.get('ingredients'):
                return {item_id: multiplier}

            totals = {}
            for ingredient in item_data['ingredients']:
                sub_item = ingredient['item']
                sub_amount = ingredient['amount'] * multiplier
                sub_totals = Hypixel.Forge.get_total_ingredients(sub_item, sub_amount)
                for k, v in sub_totals.items():
                    totals[k] = totals.get(k, 0) + v
            return totals

        @staticmethod
        def generate_recipe_tree(item_id, amount=1):
            """
            Instead of printing to terminal, this builds a nested Python list/dict
            structure that your HTML template can effortlessly loop through.
            """
            item_data = Hypixel.Item.fetch(item_id)

            node = {
                "item_id": item_id,
                "amount": amount,
                "ingredients": []
            }

            if not item_data or not item_data.get('ingredients'):
                return node

            for ingredient in item_data['ingredients']:
                sub_tree = Hypixel.Forge.generate_recipe_tree(
                    ingredient['item'],
                    amount=ingredient['amount'] * amount
                )
                node["ingredients"].append(sub_tree)

            return node
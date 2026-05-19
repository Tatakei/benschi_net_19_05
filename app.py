from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import secrets
import yaml
import os
import requests
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BAZAAR_API = "https://api.hypixel.net/v2/skyblock/bazaar"
ITEMS_API = "https://api.hypixel.net/v2/resources/skyblock/items"

cache = {"data": [], "last_updated": 0}

PERMISSION_LEVELS = {
    "user": "f067221172bf2ea28ff4d82e8566e874c0d372dbba47d95ef06b0926ca5f7bb5",
    "advanced": "2b56b67e26a620687b24e0bef85a3b530eeb7abfd07ae6556bc20ae45f2688f5",
    "admin": "ad8007513b027a9036c83976bb99d6e52b935503ac1d0c45549228eb3bf39a3d"
}

PERM_MAP = {
    PERMISSION_LEVELS["user"]: ["bazaar"],
    PERMISSION_LEVELS["advanced"]: ["minecraft", "bazaar"],
    PERMISSION_LEVELS["admin"]: ["admin"]
}

@app.context_processor
def inject_permissions():
    def has_perm(perm_name):
        user_hash = request.cookies.get('user_perm')
        user_capabilities = PERM_MAP.get(user_hash, [])
        if "admin" in user_capabilities:
            return True
        return perm_name in user_capabilities
    return dict(has_perm=has_perm)

USERS = {
    "tatakei1": {
        "email": "tatakei1@benschi.io",
        "pw": "DQ5ijmNLqewBqJ7wX3nR1iczRM6vBfwWDyPxKPca5KUJgX6fc25JborVKUKSObZz",
        "perm": PERMISSION_LEVELS["admin"]
    },
    "folwer08": {
        "email": "folwer08@benschi.io",
        "pw": "ZBG5ZqZtliI39vBpzivEgfEHlOCWceq6JkhZSb18nJT8POLa4C3eLZTF8NIQpj22",
        "perm": PERMISSION_LEVELS["advanced"]
    },
    "hafemi": {
        "email": "hafemi@gmail.com",
        "pw": "vQTHK0CEUR4wqvRwWSPZ7oWyZBTg7ihmMjvtCtxo8fzWXn47mdb09mljPxa6LBF8",
        "perm": PERMISSION_LEVELS["user"]
    }
}

def get_data():
    now = time.time()
    if cache["data"] and (now - cache["last_updated"] < 30):
        return cache["data"], cache["last_updated"]
    try:
        bazaar_products = requests.get(BAZAAR_API, timeout=5).json().get("products", {})
        items_data = requests.get(ITEMS_API, timeout=5).json().get("items", [])
        npc_prices = {i["id"]: i.get("npc_sell_price", 0) for i in items_data}
        processed_items = []
        for key, val in bazaar_products.items():
            quick = val.get("quick_status", {})
            npc_price = npc_prices.get(key, 0)
            if npc_price == 0 or (quick.get("buyOrders") == 0 and quick.get("sellOrders") == 0):
                continue
            buy_order_price = quick.get("sellPrice", 0)
            sell_order_price = quick.get("buyPrice", 0)
            profit = npc_price - buy_order_price
            if profit <= 0: continue
            processed_items.append({
                "id": key, "name": key.replace('_', ' ').title(),
                "buy_order": buy_order_price, "sell_order": sell_order_price,
                "npc_price": npc_price, "profit": profit
            })
        cache.update({"data": processed_items, "last_updated": now})
        return processed_items, now
    except Exception:
        return cache["data"], cache["last_updated"]

def load_data():
    if not os.path.exists('storage.yaml'): return {}
    with open('storage.yaml', 'r') as file:
        return yaml.safe_load(file) or {}

def save_data(data):
    with open('storage.yaml', 'w') as file:
        yaml.dump(data, file, sort_keys=False, default_flow_style=False, indent=2)

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes:
        if 'user' not in session or not request.cookies.get('user_perm'):
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username]['pw'] == password:
            session['user'] = username
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('user_perm', USERS[username]['perm'], httponly=True, samesite='Lax')
            return resp
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('user_perm')
    return resp

@app.route('/')
def index():
    sort_order = request.args.get("sort", "desc")
    budget = request.args.get("budget", type=float)
    search_query = request.args.get("search", "").lower()

    items, last_updated = get_data()

    filtered = items
    if budget:
        filtered = [i for i in filtered if i["buy_order"] <= budget]
    if search_query:
        filtered = [i for i in filtered if search_query in i["name"].lower()]

    filtered.sort(key=lambda x: x["profit"], reverse=(sort_order == "desc"))

    return render_template("index.html",
                           items=filtered,
                           sort=sort_order,
                           budget=budget,
                           search=search_query)

@app.route('/data/get')
def data_get():
    return jsonify(load_data())

@app.route('/data/save', methods=['POST'])
def data_save():
    incoming = request.json
    category, label, freq = incoming.get('category'), incoming.get('label'), incoming.get('freq')
    raw_data = load_data()
    if category not in raw_data: raw_data[category] = []
    all_items = [item for cat in raw_data.values() for item in cat]
    next_id = max([i.get('id', 0) for i in all_items]) + 1 if all_items else 100000
    raw_data[category].append({
        "id": next_id, "freq": int(freq), "label": label, "user": session.get('user')
    })
    save_data(raw_data)
    return jsonify({"message": "Success"}), 200

@app.route('/data/edit', methods=['POST'])
def data_edit():
    incoming = request.json
    item_id, new_label, new_freq = incoming.get('id'), incoming.get('label'), incoming.get('freq')
    raw_data = load_data()
    for cat in raw_data:
        for item in raw_data[cat]:
            if item['id'] == item_id:
                item['label'] = new_label
                item['freq'] = int(new_freq)
                save_data(raw_data)
                return jsonify({"message": "Updated"}), 200
    return jsonify({"message": "Not found"}), 404

@app.route('/data/delete', methods=['POST'])
def data_delete():
    item_id = request.json.get('id')
    raw_data = load_data()
    for cat in raw_data:
        raw_data[cat] = [i for i in raw_data[cat] if i['id'] != item_id]
    save_data(raw_data)
    return jsonify({"message": "Deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
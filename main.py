import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")
print(f"CHANNEL_ID: {CHANNEL_ID}")

def get_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10)
        data = r.json()
        btc = data['bitcoin']['usd']
        eth = data['ethereum']['usd']
        return f"🚀 Crypto Price Update\n\n₿ Bitcoin: ${btc}\nΞ Ethereum: ${eth}\n\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        print(f"Price fetch error: {e}")
        return None

def send_to_telegram(msg):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: BOT_TOKEN or CHANNEL_ID missing!")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg}, timeout=10)
        print(f"Telegram response: {resp.text}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def price_loop():
    print("Price loop started!")
    while True:
        try:
            print("Checking price...")
            msg = get_price()
            if msg:
                send_to_telegram(msg)
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(300)

threading.Thread(target=price_loop, daemon=True).start()
print("Thread started!")

@app.route('/')
def home():
    return "Bot is running! 🚀"

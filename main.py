import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def get_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
        data = r.json()
        btc = data['bitcoin']['usd']
        eth = data['ethereum']['usd']
        return f"🚀 Crypto Price Update\n\n₿ Bitcoin: ${btc}\nΞ Ethereum: ${eth}\n\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Error: {e}"

def send_to_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})
        print("Sent to Telegram!")
    except Exception as e:
        print(f"Telegram Error: {e}")

def price_loop():
    while True:
        print("Checking price...")
        msg = get_price()
        send_to_telegram(msg)
        time.sleep(300)  # 5 mins ki okasari

# Start loop in background
threading.Thread(target=price_loop, daemon=True).start()

@app.route('/')
def home():
    return "Bot is running! 🚀"

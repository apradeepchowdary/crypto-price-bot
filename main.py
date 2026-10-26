import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}", flush=True)
print(f"CHANNEL_ID: {CHANNEL_ID}", flush=True)

def get_price():
    try:
        print("Fetching price from Binance...", flush=True)
        # Binance API - No limit, always works
        r = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]',
            timeout=15
        )
        print(f"Binance status: {r.status_code}", flush=True)
        data = r.json()
        # data = [{"symbol":"BTCUSDT","price":"..."}, {"symbol":"ETHUSDT","price":"..."}]
        btc = float(data[0]['price']) if data[0]['symbol']=='BTCUSDT' else float(data[1]['price'])
        eth = float(data[1]['price']) if data[1]['symbol']=='ETHUSDT' else float(data[0]['price'])
        
        msg = f"🚀 Crypto Price Update\n\n₿ Bitcoin: ${btc:,.2f}\nΞ Ethereum: ${eth:,.2f}\n\n⏰ Auto every 5 mins"
        print(f"Price msg ready: {msg}", flush=True)
        return msg
    except Exception as e:
        print(f"Price fetch error: {e}", flush=True)
        # Fallback to CoinGecko with delay
        try:
            time.sleep(2)
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=15)
            if r.status_code == 200:
                d = r.json()
                btc = d['bitcoin']['usd']
                eth = d['ethereum']['usd']
                return f"🚀 Crypto Price Update\n\n₿ Bitcoin: ${btc:,.2f}\nΞ Ethereum: ${eth:,.2f}"
        except:
            pass
        return None

def send_to_telegram(msg):
    try:
        if not BOT_TOKEN or not CHANNEL_ID:
            print("Missing BOT_TOKEN or CHANNEL_ID", flush=True)
            return
        chat_id = CHANNEL_ID.strip()
        if not chat_id.startswith("@") and not chat_id.startswith("-"):
            chat_id = "@" + chat_id
        print(f"Sending to: {chat_id}", flush=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg}
        resp = requests.post(url, json=payload, timeout=15)
        print(f"Telegram response: {resp.text}", flush=True)
    except Exception as e:
        print(f"Telegram send error: {e}", flush=True)

def price_loop():
    print("Price loop started!", flush=True)
    time.sleep(10)
    while True:
        try:
            print("Checking price...", flush=True)
            msg = get_price()
            if msg:
                send_to_telegram(msg)
            else:
                print("No price msg, skipping", flush=True)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
        print("Sleeping 300 sec...", flush=True)
        time.sleep(300)

threading.Thread(target=price_loop, daemon=True).start()
print("Thread started!", flush=True)

@app.route("/")
def home():
    return "Bot Running! Price loop active."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

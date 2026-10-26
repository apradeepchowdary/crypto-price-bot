import os, time, threading, requests
from flask import Flask
app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
def get_price():
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT"]', timeout=15)
        data = r.json()
        btc = float(data[0]['price']) if data[0]['symbol']=='BTCUSDT' else float(data[1]['price'])
        eth = float(data[1]['price']) if data[1]['symbol']=='ETHUSDT' else float(data[0]['price'])
        return f"🚀 Crypto Price Update\n\n₿ Bitcoin: ${btc:,.2f}\nΞ Ethereum: ${eth:,.2f}\n\n⏰ Auto every 5 mins"
    except Exception as e:
        print(f"Error: {e}")
        return None
def send_to_telegram(msg):
    try:
        chat_id = CHANNEL_ID.strip()
        if not chat_id.startswith("@") and not chat_id.startswith("-"):
            chat_id = "@" + chat_id
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=15)
    except Exception as e:
        print(f"Send error: {e}")
def price_loop():
    time.sleep(10)
    while True:
        msg = get_price()
        if msg:
            send_to_telegram(msg)
        time.sleep(300)
threading.Thread(target=price_loop, daemon=True).start()
@app.route("/")
def home():
    return "Bot Running!"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

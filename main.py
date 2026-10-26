import requests, time, os
from datetime import datetime
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot LIVE"

def get_prices():
    coins = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]
    url = "https://api.binance.com/api/v3/ticker/price"
    try:
        r = requests.get(url,timeout=5).json()
        price_map = {item['symbol']: float(item['price']) for item in r}
        return {c.replace('USDT',''): price_map.get(c,0) for c in coins}
    except:
        return None

def bot_loop():
    last_msg_id = None
    while True:
        try:
            prices = get_prices()
            if not prices:
                time.sleep(60)
                continue
            now = datetime.now().strftime("%d %b, %I:%M %p IST")
            msg = f"📊 CRYPTO LIVE PRICES\n\n₿ BTC: ${prices['BTC']:,.2f}\n♦️ ETH: ${prices['ETH']:,.2f}\n🔶 BNB: ${prices['BNB']:,.2f}\n☀️ SOL: ${prices['SOL']:,.2f}\n💧 XRP: ${prices['XRP']:,.4f}\n\n⏰ Updated: {now}\n🤖 Auto every 1 min | Binance"
            if last_msg_id is None:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                r = requests.post(url,data={"chat_id": CHANNEL_ID,"text": msg}).json()
                if r.get('ok'):
                    last_msg_id = r['result']['message_id']
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                requests.post(url,data={"chat_id": CHANNEL_ID,"message_id": last_msg_id,"text": msg})
        except Exception as e:
            print(e)
        time.sleep(60)

threading.Thread(target=bot_loop,daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=10000)

import os, time, threading, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = {
    "BTC-USD": "₿ Bitcoin",
    "ETH-USD": "Ξ Ethereum", 
    "BNB-USD": "BNB",
    "SOL-USD": "◎ Solana",
    "XRP-USD": "✕ Ripple",
    "DOGE-USD": "Ð Dogecoin"
}

def get_all_prices():
    prices = {}
    for symbol in COINS:
        try:
            r = requests.get(f'https://api.coinbase.com/v2/prices/{symbol}/spot', timeout=10).json()
            prices[symbol] = float(r['data']['amount'])
        except:
            prices[symbol] = 0
    return prices

def create_chart():
    try:
        r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600', timeout=15).json()
        closes = [c[4] for c in r[:24]][::-1]
        
        plt.figure(figsize=(10, 3.5), facecolor='#131b2e')
        ax = plt.gca()
        ax.set_facecolor('#131b2e')
        
        # Proper scaling - not 0 to 80k
        plt.plot(closes, color='#f7931a', linewidth=2.2)
        plt.fill_between(range(len(closes)), closes, alpha=0.15, color='#f7931a')
        
        plt.title('BTC Last 24H', color='#8a8fa8', fontsize=10, pad=10)
        plt.xticks([])
        plt.yticks([])
        plt.box(False)
        
        # Auto zoom
        min_p = min(closes) * 0.999
        max_p = max(closes) * 1.001
        plt.ylim(min_p, max_p)
        
        plt.tight_layout()
        path = '/tmp/btc_chart.png'
        plt.savefig(path, dpi=200, facecolor='#131b2e', bbox_inches='tight', pad_inches=0.1)
        plt.close()
        return path
    except Exception as e:
        print(f"Chart error: {e}")
        return None

def format_msg(prices):
    # UTC TIME
    utc_time = datetime.utcnow().strftime('%H:%M UTC')
    msg = f"🚀 CRYPTO MOMENTUM - {utc_time}\n\n"
    for sym, name in COINS.items():
        price = prices.get(sym, 0)
        if price:
            if "DOGE" in sym or "XRP" in sym:
                msg += f"{name}: ${price:.4f}\n"
            else:
                msg += f"{name}: ${price:,.2f}\n"
    msg += f"\n📊 24H BTC Momentum\n⏰ Auto every 5 mins"
    return msg

def send_to_telegram(prices, chart_path):
    try:
        chat_id = CHANNEL_ID.strip()
        if not chat_id.startswith("@") and not chat_id.startswith("-"):
            chat_id = "@" + chat_id
        msg = format_msg(prices)
        if chart_path and os.path.exists(chart_path):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as f:
                files = {'photo': f}
                data = {'chat_id': chat_id, 'caption': msg}
                requests.post(url, data=data, files=files, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=15)
    except Exception as e:
        print(f"Send error: {e}")

def price_loop():
    time.sleep(10)
    while True:
        prices = get_all_prices()
        chart = create_chart()
        send_to_telegram(prices, chart)
        time.sleep(300)

threading.Thread(target=price_loop, daemon=True).start()

@app.route("/")
def home():
    return "Pro Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

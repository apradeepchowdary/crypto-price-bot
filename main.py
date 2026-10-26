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
        
        plt.figure(figsize=(10, 4), facecolor='#0f172a')
        ax = plt.gca()
        ax.set_facecolor('#0f172a')
        
        plt.plot(closes, color='#f7931a', linewidth=2.5)
        plt.fill_between(range(len(closes)), closes, alpha=0.2, color='#f7931a')
        
        plt.title(f'BTC 24H - ${closes[-1]:,.0f}', color='white', fontsize=14, fontweight='bold')
        plt.ylabel('Price', color='gray')
        plt.xticks(color='gray')
        plt.yticks(color='gray')
        plt.grid(True, alpha=0.15, color='white')
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
        
        plt.tight_layout()
        path = '/tmp/btc_chart.png'
        plt.savefig(path, dpi=150, facecolor='#0f172a')
        plt.close()
        return path
    except Exception as e:
        print(f"Chart error: {e}")
        return None

def format_msg(prices):
    msg = f"🚀 CRYPTO MOMENTUM - {datetime.now().strftime('%I:%M %p')}\n\n"
    for sym, name in COINS.items():
        price = prices.get(sym, 0)
        if price:
            if "DOGE" in sym or "XRP" in sym:
                msg += f"{name}: ${price:.4f}\n"
            else:
                msg += f"{name}: ${price:,.2f}\n"
    msg += f"\n💹 BTC 24H Momentum\n⏰ Auto every 5 mins"
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

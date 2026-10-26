import os, time, threading, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
        candles = r[:24][::-1]  # Last 24 hours
        
        fig, ax = plt.subplots(figsize=(12, 6.5), facecolor='#131b2e')
        ax.set_facecolor('#131b2e')
        
        for i, c in enumerate(candles):
            t, low, high, open_p, close_p, vol = c
            color = '#26a69a' if close_p >= open_p else '#ef5350'  # Green up, Red down
            # Wick
            ax.plot([i, i], [low, high], color=color, linewidth=1.2)
            # Body
            body_height = abs(close_p - open_p)
            body_bottom = min(open_p, close_p)
            rect = plt.Rectangle((i-0.35, body_bottom), 0.7, max(body_height, (high-low)*0.015), 
                                 facecolor=color, edgecolor=color)
            ax.add_patch(rect)
        
        # LOGO WATERMARK - White box
        ax.text(0.5, 0.92, '@Cryptopricemomentum', 
                transform=ax.transAxes,
                fontsize=13, color='#131b2e', fontweight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='none', alpha=0.95))
        
        ax.set_title('BTC 24H CANDLE CHART', color='#8a8fa8', fontsize=11, pad=20)
        ax.set_xlim(-1, len(candles))
        ax.tick_params(colors='#a0a0a0', labelsize=9)
        ax.yaxis.tick_right()
        for spine in ax.spines.values():
            spine.set_color('#334155')
        ax.grid(True, alpha=0.15, color='white', linestyle='--')
        
        plt.tight_layout()
        path = '/tmp/btc_candle.png'
        plt.savefig(path, dpi=250, facecolor='#131b2e', bbox_inches='tight')
        plt.close()
        return path
    except Exception as e:
        print(f"Chart error: {e}")
        return None

def format_msg(prices):
    utc_time = datetime.utcnow().strftime('%H:%M UTC')
    msg = f"🕯️ CRYPTO MOMENTUM - {utc_time}\n\n"
    for sym, name in COINS.items():
        price = prices.get(sym, 0)
        if price:
            if "DOGE" in sym or "XRP" in sym:
                msg += f"{name}: ${price:.4f}\n"
            else:
                msg += f"{name}: ${price:,.2f}\n"
    msg += f"\n📊 24H Candle Momentum\n🔗 @Cryptopricemomentum"
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
    return "Candle Bot Pro Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

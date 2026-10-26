import os, time, threading, requests
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

def get_btc_chart_url():
    try:
        # Get last 24h candles
        r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600', timeout=10).json()
        # r = [[time, low, high, open, close, volume], ...]
        closes = [c[4] for c in r[:24]][::-1] # last 24 hours
        # Create QuickChart URL
        chart_config = {
            "type": "line",
            "data": {
                "labels": [""]*len(closes),
                "datasets": [{
                    "data": closes,
                    "borderColor": "#f7931a",
                    "backgroundColor": "rgba(247,147,26,0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "legend": {"display": False},
                "scales": {"xAxes": [{"display": False}], "yAxes": [{"display": False}]},
                "title": {"display": True, "text": "BTC Last 24H"}
            }
        }
        import json, urllib.parse
        encoded = urllib.parse.quote(json.dumps(chart_config))
        return f"https://quickchart.io/chart?c={encoded}&width=600&height=300&backgroundColor=%230f172a"
    except Exception as e:
        print(f"Chart error: {e}")
        return None

def format_msg(prices):
    msg = f"🚀 **Crypto Momentum - {datetime.now().strftime('%I:%M %p')}**\n\n"
    for sym, name in COINS.items():
        price = prices.get(sym, 0)
        if price > 0:
            if "DOGE" in sym:
                msg += f"{name}: ${price:.4f}\n"
            else:
                msg += f"{name}: ${price:,.2f}\n"
    msg += f"\n📊 24H Chart - BTC Momentum\n⏰ Auto every 5 mins"
    return msg

def send_to_telegram(prices, chart_url):
    try:
        chat_id = CHANNEL_ID.strip()
        if not chat_id.startswith("@") and not chat_id.startswith("-"):
            chat_id = "@" + chat_id
        
        msg = format_msg(prices)
        
        if chart_url:
            # Send photo with caption
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            data = {"chat_id": chat_id, "photo": chart_url, "caption": msg, "parse_mode": "Markdown"}
            r = requests.post(url, json=data, timeout=20)
            print(f"Photo Response: {r.text[:200]}")
            if r.status_code != 200 or '"ok":false' in r.text:
                # Fallback to text only
                raise Exception("Photo failed")
        else:
            raise Exception("No chart")
            
    except Exception as e:
        print(f"Photo failed {e}, sending text")
        try:
            chat_id = CHANNEL_ID.strip()
            if not chat_id.startswith("@") and not chat_id.startswith("-"):
                chat_id = "@" + chat_id
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            msg = format_msg(prices)
            requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=15)
        except Exception as e2:
            print(f"Send error: {e2}")

def price_loop():
    time.sleep(10)
    while True:
        prices = get_all_prices()
        chart = get_btc_chart_url()
        send_to_telegram(prices, chart)
        time.sleep(300)

threading.Thread(target=price_loop, daemon=True).start()

@app.route("/")
def home():
    return "Pro Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

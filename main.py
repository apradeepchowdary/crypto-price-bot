import os, time, threading, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def get_btc_price():
    try:
        r = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot', timeout=10).json()
        return float(r['data']['amount'])
    except: return 80129

def get_eth_price():
    try:
        r = requests.get('https://api.coinbase.com/v2/prices/ETH-USD/spot', timeout=10).json()
        return float(r['data']['amount'])
    except: return 2319

def get_fear_greed():
    try:
        r = requests.get('https://api.alternative.me/fng/?limit=1', timeout=10).json()
        data = r['data'][0]
        return int(data['value']), data['value_classification']
    except: return 50, "Neutral"

def get_global():
    try:
        r = requests.get('https://api.coingecko.com/api/v3/global', timeout=15).json()
        data = r['data']
        total_mcap = data['total_market_cap']['usd'] / 1e12
        btc_dom = data['market_cap_percentage']['btc']
        # Altcoin = Total2 approximation
        alt_mcap = total_mcap * (100 - btc_dom) / 100
        # For trend - use market_cap_change_percentage_24h_usd
        change = data.get('market_cap_change_percentage_24h_usd', 0)
        return total_mcap, btc_dom, alt_mcap, change
    except:
        return 2.69, 59.36, 1.09, 0

def get_trending_coins():
    try:
        r = requests.get('https://api.coingecko.com/api/v3/search/trending', timeout=15).json()
        coins = [c['item']['symbol'].upper() for c in r['coins'][:4]]
        return " · ".join(coins)
    except: return "TUSDT · DODO · DOOD · ANIME"

def get_trend(change_pct=0):
    if change_pct > 1: return "Uptrend ↑"
    elif change_pct < -1: return "Downtrend ↓"
    else: return "Sideways →"

def create_candle_chart():
    try:
        r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600', timeout=15).json()
        candles = r[:24][::-1]
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='#131b2e')
        ax.set_facecolor('#131b2e')
        for i, c in enumerate(candles):
            t, low, high, open_p, close_p, vol = c
            color = '#26a69a' if close_p >= open_p else '#ef5350'
            ax.plot([i, i], [low, high], color=color, linewidth=1.2)
            body_h = abs(close_p - open_p)
            body_b = min(open_p, close_p)
            rect = plt.Rectangle((i-0.35, body_b), 0.7, max(body_h, (high-low)*0.015), facecolor=color, edgecolor=color)
            ax.add_patch(rect)
        ax.text(0.5, 0.92, '@Cryptopricemomentum', transform=ax.transAxes, fontsize=13, color='#131b2e', fontweight='bold', ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='none', alpha=0.95))
        ax.set_title('BTC 24H CANDLE CHART', color='#8a8fa8', fontsize=11, pad=20)
        ax.set_xlim(-1, len(candles))
        ax.yaxis.tick_right()
        ax.tick_params(colors='#a0a0a0', labelsize=9)
        ax.grid(True, alpha=0.15, color='white', linestyle='--')
        plt.tight_layout()
        path = '/tmp/btc_candle.png'
        plt.savefig(path, dpi=250, facecolor='#131b2e', bbox_inches='tight')
        plt.close()
        return path
    except: return None

def build_message():
    btc = get_btc_price()
    eth = get_eth_price()
    fg_value, fg_text = get_fear_greed()
    total_mcap, btc_dom, alt_mcap, mcap_change = get_global()
    trending = get_trending_coins()
    
    # Get 24h change for BTC trend (approx from candle)
    try:
        r = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false', timeout=15).json()
        btc_change = r['market_data']['price_change_percentage_24h']
        eth_change = requests.get('https://api.coingecko.com/api/v3/coins/ethereum?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false', timeout=10).json()['market_data']['price_change_percentage_24h']
    except:
        btc_change = -1.2
        eth_change = -0.8

    date_str = datetime.utcnow().strftime('%b %d, %Y')
    
    msg = f"🔊 Today's Market Overview — {date_str}\n\n"
    msg += f"BTC: ${btc:,.0f} | {get_trend(btc_change)}\n"
    msg += f"ETH: ${eth:,.0f} | {get_trend(eth_change)}\n"
    msg += f"🛡️ Fear & Greed Index: {fg_value}/100 | {fg_text}\n"
    msg += f"⚡ BTC Dominance: {btc_dom:.2f}% | {get_trend(btc_change)}\n"
    msg += f"🌐 Total Market Cap: ${total_mcap:.2f}T | {get_trend(mcap_change)}\n"
    msg += f"🟢 Altcoin Market Cap (Total2): ${alt_mcap:.2f}T | Uptrend ↑\n"
    msg += f"\n📈 On our traders' radar today: {trending} — tap to analyze\n"
    msg += f"💸 Money flow (24h): in ⬈ Made in USA +8.5%, Curve Ecosystem +3.4% · out ⬋ Yield Farming -2.4%\n"
    msg += f"\n🔗 @Cryptopricemomentum"
    return msg

def send_to_telegram():
    try:
        chat_id = CHANNEL_ID.strip()
        if not chat_id.startswith("@") and not chat_id.startswith("-"):
            chat_id = "@" + chat_id
        msg = build_message()
        chart = create_candle_chart()
        if chart:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart, 'rb') as f:
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
        send_to_telegram()
        time.sleep(3600)  # 1 hour ki okasari market overview

threading.Thread(target=price_loop, daemon=True).start()

@app.route("/")
def home():
    return "Market Overview Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

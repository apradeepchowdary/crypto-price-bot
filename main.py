import requests, time, threading
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from flask import Flask
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running!"

def get_all():
    try:
        # 1. PRICES - CoinCap (No block, No 429)
        # bitcoin,ethereum,binance-coin,solana,ripple,pax-gold
        url = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,binance-coin,solana,ripple,pax-gold"
        r = requests.get(url, timeout=10).json()['data']
        # Map id -> data
        mp = {x['id']: x for x in r}
        
        btc = float(mp['bitcoin']['priceUsd'])
        btc_ch = float(mp['bitcoin']['changePercent24Hr'])
        eth = float(mp['ethereum']['priceUsd'])
        eth_ch = float(mp['ethereum']['changePercent24Hr'])
        bnb = float(mp['binance-coin']['priceUsd'])
        bnb_ch = float(mp['binance-coin']['changePercent24Hr'])
        sol = float(mp['solana']['priceUsd'])
        sol_ch = float(mp['solana']['changePercent24Hr'])
        xrp = float(mp['ripple']['priceUsd'])
        xrp_ch = float(mp['ripple']['changePercent24Hr'])
        paxg = float(mp['pax-gold']['priceUsd'])
        paxg_ch = float(mp['pax-gold']['changePercent24Hr'])
        print("CoinCap OK", flush=True)

    except Exception as e:
        print(f"CoinCap failed {e}, using Coinbase fallback", flush=True)
        def cb_price(id):
            d = requests.get(f"https://api.coinbase.com/v2/prices/{id}-USD/spot", timeout=10).json()
            return float(d['data']['amount']), 0.0
        btc, btc_ch = cb_price("BTC")
        eth, eth_ch = cb_price("ETH")
        bnb, bnb_ch = 600.0, 0.5
        sol, sol_ch = cb_price("SOL")
        xrp, xrp_ch = cb_price("XRP")
        paxg, paxg_ch = 2700.0, 0.2

    try:
        g = requests.get("https://api.coingecko.com/api/v3/global", timeout=8).json()['data']
        total = g['total_market_cap']['usd'] / 1e12
        mcap_ch = g['market_cap_change_percentage_24h_usd']
        alt = total * (1 - g['market_cap_percentage']['btc']/100 - g['market_cap_percentage']['eth']/100)
    except:
        total, mcap_ch, alt = 2.69, -1.51, 1.09

    try:
        fng = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8).json()['data'][0]
        fg_val, fg_txt = int(fng['value']), fng['value_classification']
    except:
        fg_val, fg_txt = 48, "Neutral"

    try:
        payload = {"symbols":{"tickers":["CRYPTOCAP:BTC.D","CRYPTOCAP:USDT.D"]},"columns":["close","change"]}
        tv = requests.post("https://scanner.tradingview.com/crypto/scan", json=payload, timeout=8).json()['data']
        btc_d, btc_d_ch = tv[0]['d'][0], tv[0]['d'][1]
        usdt_d, usdt_d_ch = tv[1]['d'][0], tv[1]['d'][1]
    except:
        btc_d, btc_d_ch, usdt_d, usdt_d_ch = 60.52, -0.07, 6.84, -0.30

    return btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch

def get_btc_chart():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600"
    data = requests.get(url, timeout=10).json()
    data = sorted(data)
    times = [datetime.fromtimestamp(c[0]) for c in data[-24:]]
    closes = [c[4] for c in data[-24:]]
    plt.figure(figsize=(10,4))
    plt.plot(times, closes, linewidth=2)
    plt.title("BTC 24H Chart")
    plt.grid(True, alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.tight_layout()
    plt.savefig('chart.png')
    plt.close()

def build_msg():
    btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch = get_all()
    date = datetime.utcnow().strftime('%b %d, %Y - %H:%M UTC')
    msg = f"🔊 Today's Market Overview — {date}\n\n"
    msg += f'<a href="https://www.coingecko.com/en/coins/bitcoin">₿ BTC</a>: ${btc:,.0f} | {btc_ch:+.2f}% 24H\n'
    msg += f'<a href="https://www.coingecko.com/en/coins/ethereum">Ξ ETH</a>: ${eth:,.0f} | {eth_ch:+.2f}% 24H\n'
    msg += f'<a href="https://www.coingecko.com/en/coins/binancecoin">🔶 BNB</a>: ${bnb:,.2f} | {bnb_ch:+.2f}% 24H\n'
    msg += f'<a href="https://www.coingecko.com/en/coins/solana">◎ SOL</a>: ${sol:,.2f} | {sol_ch:+.2f}% 24H\n'
    msg += f'<a href="https://www.coingecko.com/en/coins/ripple">✖️ XRP</a>: ${xrp:.4f} | {xrp_ch:+.2f}% 24H\n'
    msg += f'<a href="https://www.coingecko.com/en/coins/pax-gold">🪙 PAXG</a>: ${paxg:,.2f} | {paxg_ch:+.2f}% 24H\n'
    msg += f"😨 Fear & Greed: {fg_val}/100 | {fg_txt}\n"
    msg += f"📈 BTC.D: {btc_d:.2f}% | {btc_d_ch:+.2f}% 24H\n"
    msg += f"💵 USDT.D: {usdt_d:.3f}% | {usdt_d_ch:+.2f}% 24H\n"
    msg += f"🌐 Total Mcap: ${total:.2f}T | {mcap_ch:+.2f}% 24H\n"
    msg += f"🔵 Altcoin Mcap: ${alt:.2f}T\n\n"
    msg += f"🔗 @Cryptopricemomentum"
    return msg

def send():
    try:
        get_btc_chart()
        msg = build_msg()
        with open('chart.png', 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                          data={"chat_id": CHAT_ID, "caption": msg, "parse_mode": "HTML"},
                          files={"photo": f}, timeout=20)
        print(f"✅ Sent at {datetime.utcnow()} SUCCESS", flush=True)
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)

def loop():
    print("⏰ Loop Started...", flush=True)
    time.sleep(10)
    while True:
        send()
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

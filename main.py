import requests, time, threading
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from flask import Flask
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("CHANNEL_ID") or os.getenv("channel_id")

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot Running! Chat: {CHAT_ID}"

def get_price_and_change():
    # Price from Coinbase + Change from CoinGecko - 100% reliable
    try:
        # Prices
        def cb(sym):
            r = requests.get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot", timeout=10).json()
            return float(r['data']['amount'])
        btc = cb("BTC")
        eth = cb("ETH")
        sol = cb("SOL")
        xrp = cb("XRP")
        paxg = cb("PAXG")
        try:
            kr = requests.get("https://api.kraken.com/0/public/Ticker?pair=BNBUSD", timeout=10).json()
            bnb = float(list(kr['result'].values())[0]['c'][0])
        except:
            bnb = 600.0

        # REAL 24H % from CoinGecko
        cg = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,ripple,pax-gold&vs_currencies=usd&include_24hr_change=true", timeout=10).json()
        btc_ch = cg['bitcoin']['usd_24h_change']
        eth_ch = cg['ethereum']['usd_24h_change']
        bnb_ch = cg['binancecoin']['usd_24h_change']
        sol_ch = cg['solana']['usd_24h_change']
        xrp_ch = cg['ripple']['usd_24h_change']
        paxg_ch = cg['pax-gold']['usd_24h_change']
        
        print(f"REAL % - BTC:{btc_ch:.2f} ETH:{eth_ch:.2f} BNB:{bnb_ch:.2f}", flush=True)
        
    except Exception as e:
        print(f"Price error: {e}", flush=True)
        btc, eth, bnb, sol, xrp, paxg = 79609, 2309, 736.8, 99.94, 1.29, 4025
        btc_ch = eth_ch = bnb_ch = sol_ch = xrp_ch = paxg_ch = 0.0

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

    total, mcap_ch, alt = 2.69, -1.51, 1.09
    return btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch

def get_btc_chart():
    try:
        data = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600", timeout=10).json()
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
    except Exception as e:
        print(f"Chart error: {e}", flush=True)

def build_msg():
    btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch = get_price_and_change()
    date = datetime.utcnow().strftime('%b %d, %Y - %H:%M UTC')
    msg = f"Today's Market Overview - {date}\n\n"
    msg += f"BTC: ${btc:,.0f} | {btc_ch:+.2f}% 24H\n"
    msg += f"ETH: ${eth:,.0f} | {eth_ch:+.2f}% 24H\n"
    msg += f"BNB: ${bnb:,.2f} | {bnb_ch:+.2f}% 24H\n"
    msg += f"SOL: ${sol:,.2f} | {sol_ch:+.2f}% 24H\n"
    msg += f"XRP: ${xrp:.4f} | {xrp_ch:+.2f}% 24H\n"
    msg += f"PAXG: ${paxg:,.2f} | {paxg_ch:+.2f}% 24H\n"
    msg += f"Fear & Greed: {fg_val}/100 | {fg_txt}\n"
    msg += f"BTC.D: {btc_d:.2f}% | {btc_d_ch:+.2f}% 24H\n"
    msg += f"USDT.D: {usdt_d:.3f}% | {usdt_d_ch:+.2f}% 24H\n"
    msg += f"Total Mcap: ${total:.2f}T | {mcap_ch:+.2f}% 24H\n"
    msg += f"Altcoin Mcap: ${alt:.2f}T\n\n"
    msg += f"@Cryptopricemomentum"
    return msg

def send():
    try:
        get_btc_chart()
        msg = build_msg()
        with open('chart.png', 'rb') as f:
            resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                          data={"chat_id": CHAT_ID, "caption": msg},
                          files={"photo": f}, timeout=20)
        print(f"Telegram: {resp.status_code} - {resp.text[:300]}", flush=True)
        print(f"✅ Sent at {datetime.utcnow()}", flush=True)
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)

def loop():
    print("Loop Started...", flush=True)
    time.sleep(10)
    while True:
        send()
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

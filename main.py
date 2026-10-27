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

def get_prices():
    try:
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
    except:
        btc, eth, bnb, sol, xrp, paxg = 79609, 2309, 736.8, 99.94, 1.29, 4025

    try:
        fng = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8).json()['data'][0]
        fg_val, fg_txt = int(fng['value']), fng['value_classification']
    except:
        fg_val, fg_txt = 48, "Neutral"

    try:
        payload = {"symbols":{"tickers":["CRYPTOCAP:BTC.D","CRYPTOCAP:USDT.D"]},"columns":["close"]}
        tv = requests.post("https://scanner.tradingview.com/crypto/scan", json=payload, timeout=8).json()['data']
        btc_d = tv[0]['d'][0]
        usdt_d = tv[1]['d'][0]
    except:
        btc_d, usdt_d = 60.52, 6.84

    total, alt = 2.69, 1.09
    return btc, eth, bnb, sol, xrp, paxg, total, alt, fg_val, fg_txt, btc_d, usdt_d

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
    except:
        pass

def build_msg():
    btc, eth, bnb, sol, xrp, paxg, total, alt, fg_val, fg_txt, btc_d, usdt_d = get_prices()
    date = datetime.utcnow().strftime('%b %d, %Y - %H:%M UTC')
    msg = f"Today's Market Overview - {date}\n\n"
    msg += f"BTC: ${btc:,.0f}\n"
    msg += f"ETH: ${eth:,.0f}\n"
    msg += f"BNB: ${bnb:,.2f}\n"
    msg += f"SOL: ${sol:,.2f}\n"
    msg += f"XRP: ${xrp:.4f}\n"
    msg += f"PAXG: ${paxg:,.2f}\n"
    msg += f"Fear & Greed: {fg_val}/100 | {fg_txt}\n"
    msg += f"BTC.D: {btc_d:.2f}%\n"
    msg += f"USDT.D: {usdt_d:.3f}%\n"
    msg += f"Total Mcap: ${total:.2f}T\n"
    msg += f"Altcoin Mcap: ${alt:.2f}T\n\n"
    msg += f"@Cryptopricemomentum\n\n"
    msg += f"#Btc #Eth #Bnb #Sol #Xrp #Paxg #Bitcoin #Ethereum #Crypto #CryptoNews #Altcoins"
    return msg

def send():
    try:
        get_btc_chart()
        msg = build_msg()
        with open('chart.png', 'rb') as f:
            resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                          data={"chat_id": CHAT_ID, "caption": msg},
                          files={"photo": f}, timeout=20)
        print(f"Telegram: {resp.status_code}", flush=True)
        print(f"✅ Sent at {datetime.utcnow()}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

def loop():
    print("Loop Started...", flush=True)
    time.sleep(10)
    while True:
        send()
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

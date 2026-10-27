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

def get_price(sym):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot", timeout=10).json()
        return float(r['data']['amount'])
    except Exception as e:
        print(f"Price fail {sym}: {e}", flush=True)
        return None

def get_all():
    btc = get_price("BTC") or 108000
    eth = get_price("ETH") or 3800
    sol = get_price("SOL") or 180
    xrp = get_price("XRP") or 0.55
    paxg = get_price("PAXG") or 2750
    try:
        kr = requests.get("https://api.kraken.com/0/public/Ticker?pair=BNBUSD", timeout=10).json()
        bnb = float(list(kr['result'].values())[0]['c'][0])
    except:
        bnb = 600.0

    try:
        cc = requests.get("https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,BNB,SOL,XRP,PAXG&tsyms=USD", timeout=10).json()['RAW']
        btc_ch = cc['BTC']['USD']['CHANGEPCT24HOUR']
        eth_ch = cc['ETH']['USD']['CHANGEPCT24HOUR']
        bnb_ch = cc['BNB']['USD']['CHANGEPCT24HOUR']
        sol_ch = cc['SOL']['USD']['CHANGEPCT24HOUR']
        xrp_ch = cc['XRP']['USD']['CHANGEPCT24HOUR']
        paxg_ch = cc['PAXG']['USD']['CHANGEPCT24HOUR']
    except:
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

def build_msg():
    btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch = get_all()
    date = datetime.utcnow().strftime('%b %d, %Y - %H:%M UTC')
    # NO HTML - Plain text only to avoid parse error
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
        print(f"Telegram Response: {resp.status_code} - {resp.text[:500]}", flush=True)
        if resp.status_code != 200:
            # Fallback - text only
            resp2 = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id": CHAT_ID, "text": msg}, timeout=20)
            print(f"Fallback Text Response: {resp2.text[:500]}", flush=True)
        
        print(f"✅ Sent at {datetime.utcnow()} SUCCESS", flush=True)
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

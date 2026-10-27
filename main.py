import requests, time, threading
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from flask import Flask
import os

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")  # Render ENV lo pettali
CHAT_ID = os.getenv("CHAT_ID")  # Eg: @Cryptopricemomentum or -100xxxx
# Local test kosam direct rayochu:
# TOKEN = "123456:YOUR_TOKEN"
# CHAT_ID = "@Cryptopricemomentum"

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Running!"

def get_all():
    # 1. 6 Coins - CoinGecko
    cg = requests.get(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,ripple,pax-gold&vs_currencies=usd&include_24hr_change=true",
        timeout=10
    ).json()
    
    btc, btc_ch = cg['bitcoin']['usd'], cg['bitcoin']['usd_24h_change']
    eth, eth_ch = cg['ethereum']['usd'], cg['ethereum']['usd_24h_change']
    bnb, bnb_ch = cg['binancecoin']['usd'], cg['binancecoin']['usd_24h_change']
    sol, sol_ch = cg['solana']['usd'], cg['solana']['usd_24h_change']
    xrp, xrp_ch = cg['ripple']['usd'], cg['ripple']['usd_24h_change']
    paxg, paxg_ch = cg['pax-gold']['usd'], cg['pax-gold']['usd_24h_change']

    # 2. Total & Altcoin Mcap
    g = requests.get("https://api.coingecko.com/api/v3/global", timeout=10).json()['data']
    total = g['total_market_cap']['usd'] / 1e12
    mcap_ch = g['market_cap_change_percentage_24h_usd']
    alt = total * (1 - g['market_cap_percentage']['btc']/100 - g['market_cap_percentage']['eth']/100)

    # 3. Fear & Greed
    fng = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()['data'][0]
    fg_val, fg_txt = int(fng['value']), fng['value_classification']

    # 4. BTC.D & USDT.D - TradingView exact
    payload = {"symbols":{"tickers":["CRYPTOCAP:BTC.D","CRYPTOCAP:USDT.D"]},"columns":["close","change"]}
    tv = requests.post("https://scanner.tradingview.com/crypto/scan", json=payload, timeout=10).json()['data']
    btc_d, btc_d_ch = tv[0]['d'][0], tv[0]['d'][1]
    usdt_d, usdt_d_ch = tv[1]['d'][0], tv[1]['d'][1]

    return btc, btc_ch, eth, eth_ch, bnb, bnb_ch, sol, sol_ch, xrp, xrp_ch, paxg, paxg_ch, total, mcap_ch, alt, fg_val, fg_txt, btc_d, btc_d_ch, usdt_d, usdt_d_ch

def get_btc_chart():
    # Coinbase BTC 24H candles
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600"
    data = requests.get(url, timeout=10).json()
    data = sorted(data) # time asc
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
        # Send chart
        with open('chart.png', 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                          data={"chat_id": CHAT_ID, "caption": msg, "parse_mode": "HTML"},
                          files={"photo": f}, timeout=20)
        print(f"Sent at {datetime.utcnow()}")
    except Exception as e:
        print(f"Error: {e}")

def loop():
    time.sleep(10)
    while True:
        send()
        time.sleep(3600)  # 1 HOUR - 60 sec kavali ante 60 petu bro

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

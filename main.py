import os, requests, re
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")
app = Flask(__name__)

def clean_text(t):
    # Ads mathrame delete
    t = re.sub(r'Rainbet\.com.*', '', t, flags=re.IGNORECASE|re.DOTALL)
    t = re.sub(r'the #1 Non-KYC.*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'http\S+|t\.me/\S+|@\w+', '', t)
    t = t.replace('Forwarded from','').replace('BRICS News','').replace('War Monitor','')
    t = t.replace('⚡','').replace('💧','').replace('🔥','').replace('JUST IN:','').replace('JUST IN','')
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:800]

def get_ai_reply(user_msg):
    clean = clean_text(user_msg)
    print(f"CLEAN: {clean}", flush=True)
    if len(clean) < 2:
        return "Bro em pampaledu, malli pampu bro!"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are GROQ AI bot. You MUST ALWAYS reply in Telugish - Telugu words written in English letters, bro style, 2-3 lines max. Example: Eroju 28th Oct 2026 bro, ippudu 8 AM ayindi, IST zone lo unnav. Netanyahu bloc munduku vellindi anta bro. For ANY question - news, date, time, time zone, greeting - reply ONLY in Telugish. Never English. If empty say: Bro ardham kaledu malli cheppu!"},
            {"role": "user", "content": clean}
        ],
        "temperature": 0.8,
        "max_tokens": 300,
        "reasoning_effort": "low"
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"STATUS: {r.status_code}", flush=True)
        print(f"RAW: {r.text[:1200]}", flush=True)
        
        data = r.json()
        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0]["message"]
            content = msg.get("content", "")
            
            # Empty fix - reasoning nundi teesuko lekapothe default
            if not content or content.strip() == "":
                content = msg.get("reasoning", "")
                # Reasoning lo kuda Telugish lekapothe maname ichestam
                if not content or len(content.strip()) < 3:
                    content = "Bro message ardham kaledu, koncham clear ga pampu bro!"
            
            return content.strip()
        else:
            err = data.get("error", {}).get("message", str(data)[:200])
            print(f"ERROR: {err}", flush=True)
            return f"Bro error vachindi: {err[:150]} - key check chey!"
            
    except Exception as e:
        print(f"EX: {e}", flush=True)
        return "Bro koncham issue vachindi, malli try chey bro!"

def send_telegram(chat_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"SEND ERR: {e}", flush=True)

@app.route('/')
def home():
    return "GROQ AI ON - Telugish Mode"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        msg = data.get("message") or data.get("channel_post") or data.get("edited_message") or data.get("edited_channel_post")
        if not msg:
            return "ok", 200
        chat_id = msg["chat"]["id"]
        text = msg.get("text") or msg.get("caption") or ""
        print(f"GOT: {text[:300]}", flush=True)
        if not text:
            return "ok", 200
            
        if text.strip() == "/start":
            send_telegram(chat_id, "Hey bro! 😎 Nenu ready! E news aina, date, time - anni Telugish lo chepta! Forward chey!")
        else:
            reply = get_ai_reply(text)
            if reply:
                send_telegram(chat_id, reply)
    except Exception as e:
        print(f"WEBHOOK ERR: {e}", flush=True)
    return "ok", 200

@app.route('/setwebhook')
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://thegroqaibot.onrender.com/webhook&drop_pending_updates=True"
    r = requests.get(url)
    return r.text

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
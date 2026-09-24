import os
import re
import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. RENDER PORT FIX (Dummy Web Server) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. SETUP ENV VARIABLES & FIREBASE ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CUELINKS_API_KEY = os.environ.get("CUELINKS_API_KEY")
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS")

if FIREBASE_CREDENTIALS and not firebase_admin._apps:
    try:
        cred_dict = json.loads(FIREBASE_CREDENTIALS)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Init Error: {e}")

db = firestore.client() if firebase_admin._apps else None

# --- 3. HELPER FUNCTION TO EXPAND SHORT LINKS & CONVERT VIA CUELINKS ---
def get_cuelinks_affiliate_url(short_url):
    # Step A: Expand short URLs (like dl.flipkart.com, amzn.to) to full URLs
    headers_browser = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(short_url, headers=headers_browser, allow_redirects=True, timeout=10)
        expanded_url = res.url
    except Exception as e:
        print(f"URL Expansion Error: {e}")
        expanded_url = short_url

    # Step B: Call Cuelinks API v2 with full URL
    api_endpoint = "https://www.cuelinks.com/api/v2/links.json"
    api_headers = {
        "Content-Type": "application/json",
        "Authorization": f'Token token="{CUELINKS_API_KEY}"'
    }
    payload = {
        "url": expanded_url
    }

    try:
        response = requests.post(api_endpoint, json=payload, headers=api_headers, timeout=10)
        data = response.json()
        print("Cuelinks Response Data:", data)
        
        if "affiliate_url" in data and data["affiliate_url"]:
            return data["affiliate_url"]
        elif "url" in data and data["url"]:
            return data["url"]
    except Exception as e:
        print(f"Cuelinks API Error: {e}")
        
    return None

# --- 4. BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(f"नमस्कार {user_first_name}! KamaiLink बॉट में आपका स्वागत है। मुझे कोई भी शॉपिंग लिंक भेजें, मैं उसे एफिलिएट लिंक में बदल दूंगा।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await update.message.reply_text("कृपया एक सही प्रोडक्ट लिंक भेजें।")
        return

    original_url = urls[0]
    await update.message.reply_text("आपका लिंक कन्वर्ट किया जा रहा है, कृपया इंतज़ार करें...")

    affiliate_url = get_cuelinks_affiliate_url(original_url)

    if affiliate_url and affiliate_url != original_url:
        await update.message.reply_text(f"आपका एफिलिएट लिंक तैयार है:\n\n{affiliate_url}")
    else:
        await update.message.reply_text("Cuelinks से लिंक कन्वर्ट नहीं हो सका। कृपया अपनी API Key या चैनल अप्रूवल चेक करें।")

# --- 5. MAIN EXECUTION ---
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

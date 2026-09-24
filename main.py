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
    cred_dict = json.loads(FIREBASE_CREDENTIALS)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client() if firebase_admin._apps else None

# --- 3. BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(f"ਨਮਸਕਾਰ {user_first_name}! ਤੁਹਾਡਾ KamaiLink ਬੋਟ ਵਿੱਚ ਸਵਾਗਤ ਹੈ। ਮੈਨੂੰ ਕੋਈ ਵੀ ਸ਼ਾਪਿੰਗ ਲਿੰਕ ਭੇਜੋ, ਮੈਂ ਉਸਨੂੰ ਅਫੀਲੀਏਟ ਲਿੰਕ 'ਚ ਬਦਲ ਦੇਵਾਂਗਾ।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await update.message.reply_text("ਕਿਰਪਾ ਕਰਕੇ ਇੱਕ ਸਹੀ ਪ੍ਰੋਡਕਟ ਲਿੰਕ ਭੇਜੋ।")
        return

    original_url = urls[0]
    await update.message.reply_text("ਤੁਹਾਡਾ ਲਿੰਕ ਕਨਵਰਟ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ, ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ...")

    # Cuelinks API call
    try:
        api_url = f"https://www.cuelinks.com/api/v2/links.json?url={original_url}&api_key={CUELINKS_API_KEY}"
        response = requests.get(api_url)
        data = response.json()
        
        affiliate_url = data.get("affiliate_url", original_url)
        await update.message.reply_text(f"ਤੁਹਾਡਾ ਅਫੀਲੀਏਟ ਲਿੰਕ ਤਿਆਰ ਹੈ:\n\n{affiliate_url}")
    except Exception as e:
        await update.message.reply_text("ਲਿੰਕ ਕਨਵਰਟ ਕਰਨ ਵੇਲੇ ਕੋਈ ਸਮੱਸਿਆ ਆਈ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਬਾਅਦ ਵਿੱਚ ਕੋਸ਼ਿਸ਼ ਕਰੋ।")

# --- 4. MAIN EXECUTION ---
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

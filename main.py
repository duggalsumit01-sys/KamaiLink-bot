import os
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

logging.basicConfig(level=logging.INFO)

# Firebase Init
cred_json = os.environ.get("FIREBASE_CREDENTIALS")
if cred_json:
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CUELINKS_API_KEY = os.environ.get("CUELINKS_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_ref = db.collection("users").document(str(user.id))
    
    if not user_ref.get().exists:
        user_ref.set({
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0.0,
            "joined_at": firestore.SERVER_TIMESTAMP
        })
    
    await update.message.reply_text(f"नमस्कार {user.first_name}! KamaiLink ਬੋਟ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ।")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

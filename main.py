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

async def handle_message(update: Update,

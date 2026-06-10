import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

VIP_CHANNEL_ID = -6884094503  # ⬅️ ΒΑΛΕ ΤΟ ΣΩΣΤΟ ID ΣΟΥ
PAYPAL_EMAIL = "leonidacc7@gmail.com"

# ---------------- DB ----------------
conn = sqlite3.connect("vip.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    expires_at TEXT
)
""")
conn.commit()

pending = {}

# ---------------- PLANS ----------------
PLANS = {
    "vip_1m": (10, 30),
    "vip_3m": (25, 90),
    "vip_6m": (50, 180)
}

# ---------------- VIP HELPERS ----------------
def set_vip(user_id, days):
    expire = datetime.datetime.now() + datetime.timedelta(days=days)
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, expires_at) VALUES (?, ?)",
        (user_id, expire.isoformat())
    )
    conn.commit()

def get_expiry(user_id):
    cursor.execute("SELECT expires_at FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return datetime.datetime.fromisoformat(row[0])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 1 Month - 10€", callback_data="vip_1m")],
        [InlineKeyboardButton("🔥 3 Months - 25€", callback_data="vip_3m")],
        [InlineKeyboardButton("👑 6 Months - 50€", callback_data="vip_6m")]
    ]

    await update.message.reply_text(
        "🔥 VIP SUBSCRIPTION\n\nChoose your plan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- MY PLAN ----------------
async def myplan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    exp = get_expiry(user_id)

    if not exp:
        await update.message.reply_text("❌ You are not VIP.")
        return

    remaining = exp - datetime.datetime.now()

    await update.message.reply_text(
        f"💎 VIP ACTIVE\n\nExpires: {exp.strftime('%Y-%m-%d')}\nDays left: {remaining.days}"
    )

# ---------------- BUTTONS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # ---------------- PLAN SELECT ----------------
    if query.data in PLANS:
        price, days = PLANS[query.data]
        pending[user_id] = days

        await query.message.reply_text(
            f"💳 Pay via PayPal:\n\n"
            f"{price}€ → {PAYPAL_EMAIL}\n\n"
            f"⚠️ IMPORTANT:\n"
            f'Write in payment note: "BetHunetrs VIP"\n\n'
            f"After payment type /paid"
        )

    # ---------------- APPROVE PAYMENT ----------------
    elif query.data.startswith("approve_"):
        target = int(query.data.split("_")[1])
        days = pending.get(target, 30)

        set_vip(target, days)

        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=VIP_CHANNEL_ID,
                member_limit=1
            )

            await context.bot.send_message(
                chat_id=target,
                text=f"🎉 VIP Activated!\n\nHere is your access link:\n{invite.invite_link}"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=target,
                text="VIP activated but link failed. Contact admin."
            )

        await query.message.reply_text("✅ Approved")

# ---------------- PAID ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending:
        await update.message.reply_text("❌ No pending payment.")
        return

    keyboard = [
        [InlineKeyboardButton("✅ APPROVE USER", callback_data=f"approve_{user_id}")]
    ]

    await update.message.reply_text(
        f"💰 Payment request from {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("myplan", myplan))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()

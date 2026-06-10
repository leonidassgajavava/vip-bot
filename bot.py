import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

VIP_CHANNEL_LINK = "https://t.me/+hfF2DPLqTgRmMzQ0"  # ⬅️ βάλε manual invite link

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

# ---------------- PLAN HANDLER ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in PLANS:
        price, days = PLANS[query.data]
        pending[user_id] = days

        await query.message.reply_text(
            f"💳 Pay via PayPal:\n\n"
            f"{price}€ to your PayPal email\n\n"
            f"⚠️ IMPORTANT: write 'BetHunetrs VIP' in note\n\n"
            f"After payment type /paid"
        )

# ---------------- PAID CONFIRM ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending:
        await update.message.reply_text("❌ No pending payment.")
        return

    await update.message.reply_text(
        "🎉 Payment received!\n\n"
        f"👉 Join VIP here:\n{VIP_CHANNEL_LINK}"
    )

# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()

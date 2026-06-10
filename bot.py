import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")

VIP_CHANNEL_ID = -1003951903278  # ⬅️ βάλε το σωστό channel id
PAYPAL_EMAIL = "leonidacc7@gmail.com"
ADMIN_ID = 6884094503  # ⬅️ βάλε το Telegram ID σου

# ---------------- DATABASE ----------------
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

# ---------------- BUTTONS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in PLANS:
        price, days = PLANS[query.data]
        pending[user_id] = days

        await query.message.reply_text(
            f"💳 Pay via PayPal:\n\n"
            f"{price}€ → {PAYPAL_EMAIL}\n\n"
            f"⚠️ Write in note: your USER ID\n\n"
            f"After payment send /paid"
        )

    elif query.data.startswith("approve_"):
        target = int(query.data.split("_")[1])
        days = pending.get(target, 30)

        expire = datetime.datetime.now() + datetime.timedelta(days=days)

        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, expires_at) VALUES (?, ?)",
            (target, expire.isoformat())
        )
        conn.commit()

        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=VIP_CHANNEL_ID,
                member_limit=1
            )

            await context.bot.send_message(
                chat_id=target,
                text=f"🎉 VIP ACTIVATED!\n\nHere is your access link:\n{invite.invite_link}"
            )

        except Exception:
            await context.bot.send_message(
                chat_id=target,
                text="VIP activated but invite link failed."
            )

        await query.message.reply_text("✅ Approved")

# ---------------- PAID ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending:
        await update.message.reply_text("❌ No pending payment.")
        return

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💰 PAYMENT REQUEST\nUser ID: {user_id}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{user_id}")]
        ])
    )

    await update.message.reply_text("⏳ Waiting for admin approval...")

# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()

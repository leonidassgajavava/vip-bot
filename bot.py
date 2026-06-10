import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")

VIP_CHANNEL_ID = -1003951903278
PAYPAL_EMAIL = "leonidacc7@gmail.com"
ADMIN_ID = 6884094503

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
    "vip_trial": (5, 15),
    "vip_1m": (10, 30),
    "vip_3m": (25, 90),
    "vip_6m": (50, 180)
}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🧪 Trial 15 Days - 5€", callback_data="vip_trial")],
        [InlineKeyboardButton("💎 1 Month - 10€", callback_data="vip_1m")],
        [InlineKeyboardButton("🔥 3 Months - 25€", callback_data="vip_3m")],
        [InlineKeyboardButton("👑 6 Months - 50€", callback_data="vip_6m")]
    ]

    await update.message.reply_text(
        "🔥 BETHUNETRS VIP\n\nChoose your subscription:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- MY PLAN ----------------
async def myplan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
        "SELECT expires_at FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    if not row:
        await update.message.reply_text(
            "❌ You don't have an active VIP subscription."
        )
        return

    expiry = datetime.datetime.fromisoformat(row[0])

    remaining = expiry - datetime.datetime.now()

    if remaining.total_seconds() <= 0:
        await update.message.reply_text(
            "❌ Your VIP subscription has expired."
        )
        return

    await update.message.reply_text(
        f"💎 VIP Subscription\n\n"
        f"📅 Expires: {expiry.strftime('%d/%m/%Y')}\n"
        f"⏳ Days Remaining: {remaining.days}"
    )

# ---------------- BUTTONS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # BUY PLAN
    if query.data in PLANS:

        price, days = PLANS[query.data]

        pending[user_id] = days

        await query.message.reply_text(
            f"💳 Pay via PayPal\n\n"
            f"Send {price}€ to:\n"
            f"{PAYPAL_EMAIL}\n\n"
            f"⚠️ IMPORTANT:\n"
            f"Write your Telegram User ID in the payment note.\n\n"
            f"After payment send:\n"
            f"/paid"
        )

    # APPROVE USER
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
                text=(
                    "🎉 VIP ACTIVATED!\n\n"
                    f"Join here:\n{invite.invite_link}\n\n"
                    f"Use /myplan anytime to check your subscription."
                )
            )

        except Exception as e:

            await context.bot.send_message(
                chat_id=target,
                text=f"❌ Invite link failed.\n\nError:\n{e}"
            )

        await query.message.reply_text("✅ User approved")

# ---------------- PAID ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id not in pending:

        await update.message.reply_text(
            "❌ No pending payment found."
        )
        return

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💰 NEW PAYMENT REQUEST\n\n"
            f"User ID: {user_id}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"approve_{user_id}"
                )
            ]
        ])
    )

    await update.message.reply_text(
        "⏳ Payment request sent to admin.\n\n"
        "Please wait for approval."
    )

async def vipusers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT user_id, expires_at FROM users"
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No VIP users.")
        return

    text = "💎 VIP USERS\n\n"

    for user_id, expires_at in rows:
        text += f"{user_id} → {expires_at}\n"

    await update.message.reply_text(text)


async def expired(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    now = datetime.datetime.now()

    cursor.execute(
        "SELECT user_id, expires_at FROM users"
    )

    rows = cursor.fetchall()

    expired_users = []

    for user_id, expires_at in rows:

        expiry = datetime.datetime.fromisoformat(expires_at)

        if expiry <= now:
            expired_users.append(str(user_id))

    if not expired_users:
        await update.message.reply_text(
            "✅ No expired subscriptions."
        )
        return

    await update.message.reply_text(
        "❌ Expired Users:\n\n" +
        "\n".join(expired_users)
    )


# ---------------- APP ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("myplan", myplan))
app.add_handler(CommandHandler("vipusers", vipusers))
app.add_handler(CommandHandler("expired", expired))
app.add_handler(CallbackQueryHandler(button))

print("Bot started...")

app.run_polling()

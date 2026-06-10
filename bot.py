import os
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ΒΑΛΕ ΤΟ VIP CHANNEL LINK ΣΟΥ
VIP_CHANNEL_LINK = "https://t.me/+hfF2DPLqTgRmMzQ0"

pending_payments = {}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 VIP 30€ / 30 days", callback_data="vip_1")]
    ]

    await update.message.reply_text(
        "🔥 Welcome!\n\n💎 VIP Membership available\n30€/month",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTTONS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "vip_1":
        pending_payments[user_id] = True

        await query.message.reply_text(
            "💳 Pay via PayPal:\n\n"
            "Send 30€ to: leonidacc7@gmail.com\n\n"
            "After payment type /paid"
        )

    elif query.data.startswith("approve_"):
        target_user = int(query.data.split("_")[1])

        await context.bot.send_message(
            chat_id=target_user,
            text=f"🎉 Payment approved!\n\nJoin VIP here:\n{VIP_CHANNEL_LINK}"
        )

        await query.message.reply_text("✅ User approved and invited to VIP.")

# ---------------- PAID ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending_payments:
        await update.message.reply_text("❌ No pending payment found.")
        return

    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")]
    ]

    await update.message.reply_text(
        f"💰 Payment request from user {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- MAIN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
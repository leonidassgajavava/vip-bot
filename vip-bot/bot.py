from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
VIP_CHANNEL_LINK = "https://t.me/YOUR_VIP_CHANNEL"

pending_payments = {}
vip_users = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 VIP 30€ / 30 days", callback_data="buy")]
    ]
    await update.message.reply_text(
        "Welcome!\n\n💎 VIP Membership: 30€/month",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# button handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "buy":
        pending_payments[user_id] = True

        await query.message.reply_text(
            "💳 Pay via PayPal:\n\n"
            "Send 30€ to: YOUR_PAYPAL_EMAIL\n\n"
            "After payment press /paid"
        )

# user says paid
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending_payments:
        await update.message.reply_text("❌ No pending payment found.")
        return

    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")]
    ]

    await update.message.reply_text(
        f"New payment request from {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# admin approves
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    expires = datetime.datetime.now() + datetime.timedelta(days=30)
    vip_users[user_id] = expires

    await query.message.reply_text(f"✅ Approved user {user_id}")

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 You are now VIP!\nJoin here: {VIP_CHANNEL_LINK}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CallbackQueryHandler(approve))

app.run_polling()
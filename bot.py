import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    await update.message.reply_text(
        f"📊 CHAT INFO\n\n"
        f"Chat Title: {chat.title}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat Type: {chat.type}\n\n"
        f"Your User ID: {user.id}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /id to get chat ID")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_id))

app.run_polling()

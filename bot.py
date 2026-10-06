import logging
import csv
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# טוקן הבוט מ-BotFather
BOT_TOKEN = "הדבק_כאן_את_הטוקן_שלך"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def save_response(user_id, username, full_name, choice):
    file_exists = os.path.isfile('responses.csv')
    with open('responses.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Date', 'User ID', 'Username', 'Name', 'Choice'])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            username,
            full_name,
            choice
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("❌ אני מסרב", callback_data="אני מסרב")],
        [InlineKeyboardButton("🚫 הלקוח ביטל", callback_data="הלקוח ביטל")],
        [InlineKeyboardButton("⚠️ לא רלוונטי", callback_data="לא רלוונטי")],
        [InlineKeyboardButton("📅 לדחות לזמן אחר", callback_data="לדחות לזמן אחר")],
        [InlineKeyboardButton("❓ אחר", callback_data="אחר")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 שלום! אנא בחר את סטטוס הפגישה/הליד:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    user = query.from_user
    
    save_response(
        user_id=user.id,
        username=user.username or "",
        full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
        choice=choice
    )

    await query.edit_message_text(
        text=f"✅ תודה! הסטטוס שנבחר ונרשם בהצלחה: *{choice}*",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🤖 הבוט פועל כעת...")
    app.run_polling()

if name == 'main':
    main()

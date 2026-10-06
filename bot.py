import os
import requests
from flask import Flask, request, jsonify
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import threading

# הגדרות טוקנים
BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwXyz" # ודא שהטוקן האמיתי שלך כאן!
AIRTABLE_PAT = os.environ.get("AIRTABLE_PAT", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME", "Leads")

app = Flask(__name__)
telegram_app = None

# 1. טיפול בלחיצה על כפתור בטלגרם
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # חילוץ הנתונים מהכפתור (action_status_recordId)
    data_parts = query.data.split("_", 2)
    if len(data_parts) < 3:
        await query.edit_message_text("שגיאה במבנה הנתונים.")
        return

    action, status, record_id = data_parts

    # עדכון ב-Airtable במידה ויש מפתחות מוגדרים
    if AIRTABLE_PAT and AIRTABLE_BASE_ID:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        payload = {"fields": {"Status": status}}
        requests.patch(url, json=payload, headers=headers)

    await query.edit_message_text(f"✅ הסטטוס עודכן ל: **{status}**")

# 2. נקודת קצה (Endpoint) לקבלת ליד מ-Airtable
@app.route('/webhook/lead', methods=['POST'])
def receive_lead():
    data = request.json or {}
    record_id = data.get('record_id', '')
    name = data.get('name', 'לקוח חדש')
    meeting_time = data.get('meeting_time', 'לא נקבע')
    call_time = data.get('call_time', 'לא נקבע')
    chat_id = data.get('telegram_id')

    if not chat_id:
        return jsonify({"error": "Missing telegram_id"}), 400

    text = (
        f"🚨 **ליד חדש נכנס!**\n\n"
        f"👤 **שם:** {name}\n"
        f"📅 **פגישה בשעה:** {meeting_time}\n"
        f"📞 **שיחה בשעה:** {call_time}\n\n"
        f"האם אתה לוקח את המשימה?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ מורשה/מאשר", callback_data=f"accept_מאשר_{record_id}"),
            InlineKeyboardButton("❌ דוחה/מסרב", callback_data=f"reject_מסרב_{record_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # שליחת ההודעה לטלגרם
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup.to_dict()
        }
    )
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def main():
    global telegram_app
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CallbackQueryHandler(button_callback))

    # הרצת Flask ברקע כדי לקבל Webhooks מ-Airtable
    threading.Thread(target=run_flask, daemon=True).start()

    # הרצת הבוט מול טלגרם
    telegram_app.run_polling()

if __name__ == "__main__":
    main()

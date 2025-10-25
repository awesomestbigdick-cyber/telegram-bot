from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3, uuid, logging

import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8300296784:AAHleBkEoDBw3V6RAybLKvBUiXY3ktmcEao"
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME") or "@magia_vostoka"

logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("promo.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS promo_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    code TEXT,
    used INTEGER DEFAULT 0,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def get_user_code(telegram_id: int):
    cur.execute("SELECT code FROM promo_codes WHERE telegram_id = ?", (telegram_id,))
    return cur.fetchone()

def save_user_code(telegram_id: int, code: str):
    cur.execute("INSERT INTO promo_codes (telegram_id, code) VALUES (?, ?)", (telegram_id, code))
    conn.commit()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎁 Получить скидку", callback_data="get_discount")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет 👋\n"
        "Подпишись на наш канал и получи скидку!\n"
        "Нажми кнопку ниже 👇",
        reply_markup=reply_markup
    )

# === обработка кнопки ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_discount":
        user_id = query.from_user.id
        existing = get_user_code(user_id)
        if existing:
            await query.edit_message_text(f"Ваш промокод: {existing[0]} (повторно не выдаётся)")
            return

        try:
            member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        except Exception as e:
            await query.edit_message_text("Не могу проверить подписку. Попробуйте позже.")
            return

        if member.status in ["member", "administrator", "creator"]:
            code = "PROMO-" + uuid.uuid4().hex[:8].upper()
            save_user_code(user_id, code)
            await query.edit_message_text(f"✅ Спасибо за подписку!\nВаш код: {code}")
        else:
            await query.edit_message_text("❌ Пожалуйста, подпишитесь на канал и попробуйте снова.")

# === MAIN ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
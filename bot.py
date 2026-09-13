import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# Преобразуем ID в числа для корректной работы Telegram API
try:
    if TARGET_CHAT_ID: TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    if ADMIN_ID: ADMIN_ID = int(ADMIN_ID)
except ValueError:
    logger.error("ID чата или админа должны быть числами!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я готов к работе.\n"
        "Отправьте /get_chat_id в группе, чтобы узнать её ID."
    )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ID этого чата: `{update.effective_chat.id}`",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id

    if not TARGET_CHAT_ID or not ADMIN_ID:
        if message.chat.type == "private":
            await message.reply_text("Ошибка: Не настроены TARGET_CHAT_ID или ADMIN_ID на Render.")
        return

    # 1. Из ЛС с ботом -> в целевую группу (Копирование с добавлением "мира")
    if message.chat.type == "private" and chat_id == ADMIN_ID:
        
        # Если это просто текст
        if message.text:
            new_text = f"{message.text} мира"
            await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=new_text)
            
        # Если это фото
        elif message.photo:
            # Берем самое лучшее качество фото (последнее в списке)
            photo_file_id = message.photo[-1].file_id
            # Формируем подпись (caption), если она есть, и добавляем "мира"
            old_caption = message.caption or ""
            new_caption = f"{old_caption} мира".strip()
            
            await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=photo_file_id, caption=new_caption)

    # 2. Из целевой группы -> вам в ЛС (Чистое копирование)
    elif chat_id == TARGET_CHAT_ID:
        # Проверяем, что сообщение НЕ от самого бота
        if message.from_user and not message.from_user.is_bot:
            
            # Автор сообщения для отметки в начале копии
            author = f"От: @{message.from_user.username or message.from_user.first_name}\n\n"
            
            # Если в группе написали текст
            if message.text:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"{author}{message.text}")
                
            # Если в группу скинули фото
            elif message.photo:
                photo_file_id = message.photo[-1].file_id
                old_caption = message.caption or ""
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=f"{author}{old_caption}")

def main():
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN отсутствует!")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    
    # Обрабатываем и Текст, и Фотографии (филтрация команд включена)
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))

    logger.info("Бот успешно запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()

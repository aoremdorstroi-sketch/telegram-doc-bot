import os
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

OUTPUT_FOLDER = "/tmp/documents"
EXPECTED_DOCS = ["Договор", "Счет", "Акт"]

# ⚠️ ВСТАВЬТЕ ВАШ ТОКЕН ОТ BOTFATHER
TELEGRAM_TOKEN = "8836273052:AAESZbsUlOxbyIes_SKBIbVhjEg0yBANjLY"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_contractor_from_filename(filename):
    match = re.search(r'\((.*?)\)', filename)
    if match:
        return match.group(1)
    return "Неизвестный"

def get_doc_type(filename):
    for doc in EXPECTED_DOCS:
        if doc in filename:
            return doc
    return "Прочее"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("📁 Бот для документов работает!")

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    filename = update.message.document.file_name
    
    contractor = get_contractor_from_filename(filename)
    doc_type = get_doc_type(filename)
    
    contractor_folder = os.path.join(OUTPUT_FOLDER, contractor)
    if not os.path.exists(contractor_folder):
        os.makedirs(contractor_folder)
    
    dest = os.path.join(contractor_folder, filename)
    file.download(dest)
    
    update.message.reply_text(f"✅ {filename}\n📁 {contractor}\n📑 {doc_type}")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    print("Бот запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

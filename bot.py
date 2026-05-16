import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

OUTPUT_FOLDER = "/tmp/documents"
EXPECTED_DOCS = ["Договор", "Счет", "Акт"]

# ⚠️ ВСТАВЬТЕ НОВЫЙ ТОКЕН ОТ BOTFATHER
TELEGRAM_TOKEN = "8836273052:AAESZbsUlOxbyIes_SKBIbVhjEg0yBANjLY"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_contractor_from_filename(filename):
    name = filename
    if "(" in name and ")" in name:
        start = name.find("(")
        end = name.find(")")
        return name[start+1:end]
    
    for doc in EXPECTED_DOCS:
        if doc in name:
            rest = name.replace(doc, "").strip()
            for i, char in enumerate(rest):
                if char.isdigit() and i > 0 and rest[i-1] in ".-":
                    rest = rest[:i-1]
                    break
            if rest and len(rest) < 50:
                return rest.strip()
    return None

def get_doc_type(filename):
    for doc in EXPECTED_DOCS:
        if doc in filename:
            return doc
    return "Прочее"

def start(update, context):
    update.message.reply_text(
        "📁 *Бот для документов*\n\n"
        "Отправь файл с именем:\n"
        "`Договор (ООО Ромашка).pdf`\n\n"
        "📋 *Команды:*\n"
        "/check *Контрагент* — проверить комплект\n"
        "/list — все контрагенты\n"
        "/get *Контрагент* — получить архив",
        parse_mode="Markdown"
    )

def handle_document(update, context):
    file = update.message.document.get_file()
    filename = update.message.document.file_name
    
    contractor = get_contractor_from_filename(filename)
    if not contractor:
        update.message.reply_text(
            "❌ Не определил контрагента.\n"
            "Используй формат: `Договор (ООО Ромашка).pdf`",
            parse_mode="Markdown"
        )
        return
    
    doc_type = get_doc_type(filename)
    contractor_folder = os.path.join(OUTPUT_FOLDER, contractor)
    if not os.path.exists(contractor_folder):
        os.makedirs(contractor_folder)
    
    dest = os.path.join(contractor_folder, filename)
    file.download(dest)
    
    update.message.reply_text(
        f"✅ *{filename}*\n📁 Контрагент: *{contractor}*\n📑 Тип: *{doc_type}*",
        parse_mode="Markdown"
    )

def check_command(update, context):
    if not context.args:
        update.message.reply_text("Укажи контрагента: `/check ООО Ромашка`", parse_mode="Markdown")
        return
    
    contractor = " ".join(context.args)
    contractor_folder = os.path.join(OUTPUT_FOLDER, contractor)
    
    if not os.path.exists(contractor_folder):
        update.message.reply_text(f"❌ Нет документов по *{contractor}*", parse_mode="Markdown")
        return
    
    files = os.listdir(contractor_folder)
    existing_docs = set()
    for f in files:
        dt = get_doc_type(f)
        if dt != "Прочее":
            existing_docs.add(dt)
    
    missing = set(EXPECTED_DOCS) - existing_docs
    
    response = f"📁 *{contractor}*\n"
    if existing_docs:
        response += f"✅ Есть: {', '.join(existing_docs)}\n"
    else:
        response += "📭 Нет документов\n"
    
    if missing:
        response += f"❌ Нет: {', '.join(missing)}"
    else:
        response += "🎉 *Полный комплект!*"
    
    update.message.reply_text(response, parse_mode="Markdown")

def list_command(update, context):
    if not os.path.exists(OUTPUT_FOLDER):
        update.message.reply_text("📭 Нет контрагентов")
        return
    
    contractors = [d for d in os.listdir(OUTPUT_FOLDER) if os.path.isdir(os.path.join(OUTPUT_FOLDER, d))]
    if not contractors:
        update.message.reply_text("📭 Нет контрагентов")
    else:
        text = "📋 *Контрагенты:*\n" + "\n".join(f"• {c}" for c in contractors)
        update.message.reply_text(text, parse_mode="Markdown")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check", check_command))
    dp.add_handler(CommandHandler("list", list_command))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    print("🤖 Бот запущен!")
    print(f"📁 Документы будут сохранены в: {OUTPUT_FOLDER}")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

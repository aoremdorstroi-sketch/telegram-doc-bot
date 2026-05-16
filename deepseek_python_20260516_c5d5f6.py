import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

OUTPUT_FOLDER = "/opt/render/project/src/documents"
EXPECTED_DOCS = ["Договор", "Счет", "Акт"]

Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

def get_contractor_from_filename(filename):
    name = Path(filename).stem
    match = re.search(r'\((.*?)\)', name)
    if match:
        return match.group(1).strip()
    for doc in EXPECTED_DOCS:
        if doc in name:
            rest = name.replace(doc, "").strip()
            rest = re.split(r'\d{2}[\.\-]\d{2}', rest)[0].strip()
            if rest and len(rest) < 50:
                return rest
    return None

def get_doc_type(filename):
    name = Path(filename).stem
    for doc in EXPECTED_DOCS:
        if doc in name:
            return doc
    return "Прочее"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 *Бот для документов*\n\n"
        "Отправь файл с именем:\n"
        "`Договор (ООО Ромашка).pdf`\n\n"
        "📋 *Команды:*\n"
        "/check *Контрагент* — проверить комплект\n"
        "/list — все контрагенты\n"
        "/get *Контрагент* — получить архив\n\n"
        "Пример: `/check ООО Ромашка`",
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    filename = update.message.document.file_name
    
    contractor = get_contractor_from_filename(filename)
    if not contractor:
        await update.message.reply_text(
            "❌ Не определил контрагента.\n"
            "Используй формат: `Договор (ООО Ромашка).pdf`",
            parse_mode="Markdown"
        )
        return
    
    doc_type = get_doc_type(filename)
    contractor_folder = Path(OUTPUT_FOLDER) / contractor
    contractor_folder.mkdir(parents=True, exist_ok=True)
    
    dest = contractor_folder / filename
    await file.download_to_drive(dest)
    
    await update.message.reply_text(
        f"✅ *{filename}*\n"
        f"📁 Контрагент: *{contractor}*\n"
        f"📑 Тип: *{doc_type}*",
        parse_mode="Markdown"
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи контрагента: `/check ООО Ромашка`", parse_mode="Markdown")
        return
    
    contractor = " ".join(context.args)
    contractor_folder = Path(OUTPUT_FOLDER) / contractor
    
    if not contractor_folder.exists():
        await update.message.reply_text(f"❌ Нет документов по *{contractor}*", parse_mode="Markdown")
        return
    
    files = list(contractor_folder.iterdir())
    existing_docs = {get_doc_type(f.name) for f in files if get_doc_type(f.name) != "Прочее"}
    missing = set(EXPECTED_DOCS) - existing_docs
    
    response = f"📁 *{contractor}*\n"
    response += f"✅ Есть: {', '.join(existing_docs) if existing_docs else 'нет'}\n"
    if missing:
        response += f"❌ Нет: {', '.join(missing)}"
    else:
        response += "🎉 *Полный комплект!*"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contractors = [d.name for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()]
    if not contractors:
        await update.message.reply_text("📭 Нет контрагентов")
    else:
        text = "📋 *Контрагенты:*\n" + "\n".join(f"• {c}" for c in contractors)
        await update.message.reply_text(text, parse_mode="Markdown")

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи контрагента: `/get ООО Ромашка`", parse_mode="Markdown")
        return
    
    contractor = " ".join(context.args)
    contractor_folder = Path(OUTPUT_FOLDER) / contractor
    
    if not contractor_folder.exists() or not list(contractor_folder.iterdir()):
        await update.message.reply_text(f"❌ Нет документов по *{contractor}*", parse_mode="Markdown")
        return
    
    # Создаём ZIP-архив
    zip_path = Path(f"/tmp/{contractor}_{int(datetime.now().timestamp())}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in contractor_folder.iterdir():
            zipf.write(file, file.name)
    
    # Отправляем архив
    with open(zip_path, 'rb') as f:
        await update.message.reply_document(
            document=f,
            filename=f"{contractor}.zip",
            caption=f"📦 Архив документов *{contractor}*",
            parse_mode="Markdown"
        )
    
    # Удаляем временный архив
    zip_path.unlink()

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("❌ Ошибка: TELEGRAM_TOKEN не задан")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("get", get_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
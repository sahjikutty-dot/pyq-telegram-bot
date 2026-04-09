import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import fitz
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")

# STEP 1: EXTRACT TEXT FROM PDF
def load_pdf():
    doc = fitz.open("data.pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append((i+1, text))
    return pages

PDF_DATA = load_pdf()

# STEP 2: SPLIT INTO QUESTIONS
def extract_questions(text):
    return re.split(r'\n\d+\.', text)

# STEP 3: TOPIC EXPANSION (VERY IMPORTANT)
def expand_topic(topic):
    topic = topic.lower()

    mapping = {
        "sex differentiation": [
            "meiosis", "oogenesis", "fertilization",
            "chromosome", "zygote", "puberty"
        ],
        "lymphatic": [
            "cancer", "metastasis", "cervix",
            "spread", "node", "parametrium"
        ]
    }

    return mapping.get(topic, [topic])

# STEP 4: SEARCH FUNCTION
def search(topic):
    keywords = expand_topic(topic)
    results = []

    for page_num, text in PDF_DATA:
        questions = extract_questions(text)

        for q in questions:
            score = 0

            for k in keywords:
                if k in q.lower():
                    score += 1

            if score > 0:
                results.append(f"Page {page_num}:\n{q.strip()}\n")

    return results

# STEP 5: TELEGRAM HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    results = search(user_input)

    if not results:
        await update.message.reply_text("No questions found.")
        return

    # OPTIONAL LIMIT
    results = results[:30]

    # SPLIT MESSAGE (FIXED PART)
    MAX_LENGTH = 4000

    messages = []
    current_msg = ""

    for r in results:
        if len(current_msg) + len(r) < MAX_LENGTH:
            current_msg += r + "\n\n"
        else:
            messages.append(current_msg)
            current_msg = r + "\n\n"

    if current_msg:
        messages.append(current_msg)

    # SEND MESSAGES
    for msg in messages:
        await update.message.reply_text(msg)

# STEP 6: RUN BOT
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running...")
app.run_polling()

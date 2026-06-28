import logging
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from prompts import SYSTEM_PROMPTS, LANGUAGE_NAMES

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8620256752:AAFHoH2m4fOCfDCQIO_1BQBxfkCV_4TuwIs"
GROQ_API_KEY = "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"
CHANNEL_ID = "@AmooPrompi"

groq_client = Groq(api_key=GROQ_API_KEY)
CHOOSE_LANG, CHOOSE_TYPE, CHOOSE_LOGO_TYPE, GET_PROMPT = range(4)

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_membership(user.id, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url="https://t.me/AmooPrompi")],[InlineKeyboardButton("عضو شدم!", callback_data="check_membership")]]
        await update.message.reply_text(f"سلام {user.first_name}!\n\nبه ربات عمو پرامپی خوش اومدی!\n\nبرای استفاده، ابتدا عضو کانال ما بشو:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    return await show_lang_menu(update, context)

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await check_membership(query.from_user.id, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url="https://t.me/AmooPrompi")],[InlineKeyboardButton("عضو شدم!", callback_data="check_membership")]]
        await query.edit_message_text("هنوز عضو نشدی!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await query.edit_message_text("عضویت تایید شد!")
    keyboard = [[InlineKeyboardButton("فارسی", callback_data="lang_fa"),InlineKeyboardButton("English", callback_data="lang_en")],[InlineKeyboardButton("Deutsch", callback_data="lang_de"),InlineKeyboardButton("Русский", callback_data="lang_ru")],[InlineKeyboardButton("Français", callback_data="lang_fr"),InlineKeyboardButton("Italiano", callback_data="lang_it")],[InlineKeyboardButton("中文", callback_data="lang_zh"),InlineKeyboardButton("हिन्दी", callback_data="lang_hi")],[InlineKeyboardButton("한국어", callback_data="lang_ko"),InlineKeyboardButton("العربية", callback_data="lang_ar")]]
    await query.message.reply_text("زبان مورد نظرت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("فارسی", callback_data="lang_fa"),InlineKeyboardButton("English", callback_data="lang_en")],[InlineKeyboardButton("Deutsch", callback_data="lang_de"),InlineKeyboardButton("Русский", callback_data="lang_ru")],[InlineKeyboardButton("Français", callback_data="lang_fr"),InlineKeyboardButton("Italiano", callback_data="lang_it")],[InlineKeyboardButton("中文", callback_data="lang_zh"),InlineKeyboardButton("हिन्दी", callback_data="lang_hi")],[InlineKeyboardButton("한국어", callback_data="lang_ko"),InlineKeyboardButton("العربية", callback_data="lang_ar")]]
    await update.message.reply_text("زبان مورد نظرت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_LANG

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    context.user_data["language"] = lang
    await query.edit_message_text(f"زبان انتخابی: {lang}")
    keyboard = [[InlineKeyboardButton("پرامپت تصویر", callback_data="type_image")],[InlineKeyboardButton("پرامپت ویدیو", callback_data="type_video")],[InlineKeyboardButton("پرامپت لوگو", callback_data="type_logo")]]
    await query.message.reply_text("نوع پرامپت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_TYPE

async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prompt_type = query.data.replace("type_", "")
    if prompt_type == "logo":
        keyboard = [[InlineKeyboardButton("فقط لوگو", callback_data="type_logo_static")],[InlineKeyboardButton("لوگو موشن", callback_data="type_logo_motion")]]
        await query.edit_message_text("نوع لوگو رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSE_LOGO_TYPE
    context.user_data["prompt_type"] = prompt_type
    await query.edit_message_text(f"نوع انتخابی: {prompt_type}")
    await query.message.reply_text("ایده‌ات رو بنویس:")
    return GET_PROMPT

async def logo_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logo_type = query.data.replace("type_", "")
    context.user_data["prompt_type"] = logo_type
    await query.edit_message_text(f"نوع انتخابی: {logo_type}")
    await query.message.reply_text("اسم برند یا توضیح لوگوت رو بنویس:")
    return GET_PROMPT

async def generate_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    lang = context.user_data.get("language", "fa")
    prompt_type = context.user_data.get("prompt_type", "image")
    type_map = {"image": "image", "video": "video", "logo_static": "logo", "logo_motion": "logo_motion"}
    system_key = type_map.get(prompt_type, "image")
    system_prompt = SYSTEM_PROMPTS[system_key]
    lang_name = LANGUAGE_NAMES.get(lang, "English")
    lang_instruction = f" IMPORTANT: Generate the prompt in {lang_name} language ONLY."
    thinking_msg = await update.message.reply_text("عمو پرامپی داره فکر می‌کنه...")
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt + lang_instruction},{"role": "user", "content": f"Transform this idea into a professional prompt: {user_input}"}],
            temperature=0.8,
            max_tokens=800
        )
        generated_prompt = response.choices[0].message.content.strip()
        await thinking_msg.delete()
        keyboard = [[InlineKeyboardButton("پرامپت جدید", callback_data="new_prompt")],[InlineKeyboardButton("منوی اصلی", callback_data="main_menu")]]
        await update.message.reply_text(f"پرامپت حرفه‌ای عمو پرامپی:\n\n{generated_prompt}\n\nکپی کن و استفاده کن!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await thinking_msg.edit_text(f"خطا: {str(e)}")
    return ConversationHandler.END

async def new_prompt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("ایده جدیدت رو بنویس:")
    return GET_PROMPT

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("پرامپت تصویر", callback_data="type_image")],[InlineKeyboardButton("پرامپت ویدیو", callback_data="type_video")],[InlineKeyboardButton("پرامپت لوگو", callback_data="type_logo")]]
    await query.message.reply_text("منوی اصلی - نوع پرامپت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_TYPE

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANG: [CallbackQueryHandler(language_chosen, pattern="^lang_")],
            CHOOSE_TYPE: [CallbackQueryHandler(type_chosen, pattern="^type_"), CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")],
            CHOOSE_LOGO_TYPE: [CallbackQueryHandler(logo_type_chosen, pattern="^type_logo_")],
            GET_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_prompt), CallbackQueryHandler(new_prompt_callback, pattern="^new_prompt$"), CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")]
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))
    logger.info("عمو پرامپی در حال اجراست...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

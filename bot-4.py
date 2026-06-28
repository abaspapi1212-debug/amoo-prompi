import os
import logging
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

groq_client = Groq(api_key=GROQ_API_KEY)

# ذخیره وضعیت کاربر
user_states = {}

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇺🇸 انگلیسی",
    "de": "🇩🇪 آلمانی",
    "ru": "🇷🇺 روسی",
    "fr": "🇫🇷 فرانسوی",
    "it": "🇮🇹 ایتالیایی",
    "zh": "🇨🇳 چینی",
    "hi": "🇮🇳 هندی",
    "ko": "🇰🇷 کره‌ای",
    "ar": "🇸🇦 عربی",
}

PROMPT_TYPES = {
    "image": "🖼 پرامپت تصویر",
    "video": "🎬 پرامپت ویدیو",
    "logo": "🎨 پرامپت لوگو",
}

LOGO_TYPES = {
    "logo_static": "🖼 لوگو ثابت",
    "logo_motion": "✨ لوگو موشن (متحرک)",
}

# سیستم‌پرامپت برای هر نوع
SYSTEM_PROMPTS = {
    "image": """You are a world-class AI image prompt engineer with 20+ years of experience in visual arts, photography, and generative AI models like Midjourney, DALL-E, and Stable Diffusion.

Your job: Take a simple, vague description and transform it into a PROFESSIONAL, DETAILED, and BEAUTIFUL image prompt.

Rules:
- Write ONLY the prompt, no explanation, no preamble
- Include: subject, style, lighting, composition, color palette, mood, camera angle, artistic references
- Use professional photography/art terminology
- Add quality boosters: (masterpiece, ultra-detailed, 8k, professional lighting, etc.)
- Match the language of the user's input
- If input is not in one of these 10 languages (Persian, English, German, Russian, French, Italian, Chinese, Hindi, Korean, Arabic), output in BOTH Persian AND English
- Make it feel like a seasoned professional wrote it""",

    "video": """You are an expert AI video prompt engineer with 20+ years in cinematography, filmmaking, and AI video generation (Sora, Runway, Kling, Pika).

Your job: Transform a simple description into a CINEMATIC, PROFESSIONAL video prompt.

Rules:
- Write ONLY the prompt, no explanation, no preamble
- Include: scene description, camera movement, lighting, mood, pace, color grading, visual style
- Add technical details: shot type, lens style, frame rate feel, transitions
- Use cinematic terminology
- Match the language of the user's input
- If input language is unknown, output in BOTH Persian AND English
- Make it feel like a professional director/cinematographer wrote it""",

    "logo_static": """You are a master brand identity designer and AI logo prompt specialist with 20+ years in graphic design, branding, and visual identity.

Your job: Transform a simple idea into a PROFESSIONAL logo design prompt.

Rules:
- Write ONLY the prompt, no explanation, no preamble
- Include: style (minimalist/modern/vintage/etc.), color palette, typography hints, symbol concept, negative space usage, scalability notes
- Add: vector-clean, professional, brand-ready
- Use design terminology
- Match the language of the user's input
- If input language is unknown, output in BOTH Persian AND English
- Make it feel like a top branding agency wrote it""",

    "logo_motion": """You are an expert motion graphics designer and animated logo specialist with 20+ years in After Effects, Cinema 4D, and AI animation tools.

Your job: Transform a simple idea into a PROFESSIONAL animated logo / logo motion prompt.

Rules:
- Write ONLY the prompt, no explanation, no preamble
- Include: animation style, easing/timing, entrance/loop/exit behavior, particle effects if any, color transitions, sound sync hints
- Add: smooth motion, professional, brand animation
- Use motion design terminology
- Match the language of the user's input
- If input language is unknown, output in BOTH Persian AND English
- Make it feel like a senior motion designer wrote it""",
}


async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی عضویت کاربر در کانال"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False


def get_language_keyboard():
    """کیبورد انتخاب زبان"""
    buttons = []
    lang_list = list(LANGUAGES.items())
    for i in range(0, len(lang_list), 2):
        row = []
        row.append(InlineKeyboardButton(lang_list[i][1], callback_data=f"lang_{lang_list[i][0]}"))
        if i + 1 < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i+1][1], callback_data=f"lang_{lang_list[i+1][0]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def get_prompt_type_keyboard():
    """کیبورد انتخاب نوع پرامپت"""
    buttons = [
        [InlineKeyboardButton("🖼 پرامپت تصویر", callback_data="type_image")],
        [InlineKeyboardButton("🎬 پرامپت ویدیو", callback_data="type_video")],
        [InlineKeyboardButton("🎨 پرامپت لوگو", callback_data="type_logo")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_logo_type_keyboard():
    """کیبورد انتخاب نوع لوگو"""
    buttons = [
        [InlineKeyboardButton("🖼 لوگو ثابت", callback_data="logo_static")],
        [InlineKeyboardButton("✨ لوگو موشن (متحرک)", callback_data="logo_motion")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_types")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_join_keyboard():
    """کیبورد عضویت در کانال"""
    buttons = [
        [InlineKeyboardButton("📢 عضویت در کانال عمو پرامپی", url=f"https://t.me/AmooPrompi")],
        [InlineKeyboardButton("✅ عضو شدم، بررسی کن!", callback_data="check_membership")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_menu_keyboard():
    """کیبورد منوی اصلی برای کاربر فعال"""
    buttons = [
        [InlineKeyboardButton("🔄 تغییر زبان", callback_data="change_language")],
        [InlineKeyboardButton("🔁 تغییر نوع پرامپت", callback_data="change_type")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(buttons)


async def generate_prompt(user_text: str, prompt_type: str, language: str) -> str:
    """تولید پرامپت حرفه‌ای با Groq"""
    system = SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["image"])
    
    lang_name = LANGUAGES.get(language, "Unknown")
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Transform this into a professional prompt (respond in {lang_name} language): {user_text}"}
            ],
            temperature=0.85,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "❌ خطا در اتصال به هوش مصنوعی. لطفاً دوباره تلاش کنید."


# ===== هندلرها =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات"""
    user = update.effective_user
    user_id = user.id
    
    # ریست وضعیت
    user_states[user_id] = {"step": "check_join"}
    
    # بررسی عضویت
    is_member = await check_membership(user_id, context)
    
    if is_member:
        user_states[user_id]["step"] = "select_language"
        await update.message.reply_text(
            f"سلام {user.first_name} عزیز! 👋\n\n"
            "به *عمو پرامپی* خوش اومدی! 🎩✨\n\n"
            "من یه متخصص ۲۰ ساله‌ام که هر ایده ساده‌ای رو به یه پرامپت حرفه‌ای تبدیل می‌کنم!\n\n"
            "🌍 اول بگو می‌خوای به چه زبانی کار کنیم:",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard()
        )
    else:
        await update.message.reply_text(
            f"سلام {user.first_name} عزیز! 👋\n\n"
            "به *عمو پرامپی* خوش اومدی! 🎩✨\n\n"
            "برای استفاده از خدمات من، باید اول عضو کانالم بشی 👇",
            parse_mode="Markdown",
            reply_markup=get_join_keyboard()
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دکمه‌های اینلاین"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in user_states:
        user_states[user_id] = {}

    # بررسی عضویت
    if data == "check_membership":
        is_member = await check_membership(user_id, context)
        if is_member:
            user_states[user_id]["step"] = "select_language"
            await query.edit_message_text(
                "✅ عضویتت تایید شد! خوش اومدی!\n\n"
                "🌍 حالا انتخاب کن می‌خوای به چه زبانی کار کنیم:",
                reply_markup=get_language_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ هنوز عضو نشدی!\n\n"
                "لطفاً اول عضو کانال بشو بعد دکمه «عضو شدم» رو بزن 👇",
                reply_markup=get_join_keyboard()
            )

    # انتخاب زبان
    elif data.startswith("lang_"):
        lang = data.replace("lang_", "")
        user_states[user_id]["language"] = lang
        user_states[user_id]["step"] = "select_type"
        lang_name = LANGUAGES.get(lang, lang)
        
        await query.edit_message_text(
            f"✅ زبان انتخابی: {lang_name}\n\n"
            "🎯 حالا نوع پرامپتت رو انتخاب کن:",
            reply_markup=get_prompt_type_keyboard()
        )

    # انتخاب نوع پرامپت
    elif data == "type_image":
        user_states[user_id]["prompt_type"] = "image"
        user_states[user_id]["step"] = "waiting_input"
        await query.edit_message_text(
            "🖼 *پرامپت تصویر* انتخاب شد!\n\n"
            "حالا ایده یا توضیح کوتاهت رو بفرست تا من یه پرامپت حرفه‌ای ازش بسازم:\n\n"
            "_مثال: یه زن ایرانی با لباس سنتی کنار دریاچه_",
            parse_mode="Markdown"
        )

    elif data == "type_video":
        user_states[user_id]["prompt_type"] = "video"
        user_states[user_id]["step"] = "waiting_input"
        await query.edit_message_text(
            "🎬 *پرامپت ویدیو* انتخاب شد!\n\n"
            "حالا ایده یا توضیح کوتاهت رو بفرست:\n\n"
            "_مثال: غروب آفتاب در کوهستان با دوربین درحال حرکت_",
            parse_mode="Markdown"
        )

    elif data == "type_logo":
        user_states[user_id]["step"] = "select_logo_type"
        await query.edit_message_text(
            "🎨 *پرامپت لوگو* انتخاب شد!\n\n"
            "چه نوع لوگویی می‌خوای؟",
            parse_mode="Markdown",
            reply_markup=get_logo_type_keyboard()
        )

    elif data == "logo_static":
        user_states[user_id]["prompt_type"] = "logo_static"
        user_states[user_id]["step"] = "waiting_input"
        await query.edit_message_text(
            "🖼 *لوگو ثابت* انتخاب شد!\n\n"
            "توضیح کوتاهی از برند یا ایده‌ات بده:\n\n"
            "_مثال: یه شرکت فناوری به اسم نووا با حس مدرن و آبی_",
            parse_mode="Markdown"
        )

    elif data == "logo_motion":
        user_states[user_id]["prompt_type"] = "logo_motion"
        user_states[user_id]["step"] = "waiting_input"
        await query.edit_message_text(
            "✨ *لوگو موشن* انتخاب شد!\n\n"
            "توضیح کوتاهی از برند یا ایده‌ات بده:\n\n"
            "_مثال: لوگوی یه کافه به اسم مون با انیمیشن ذرات قهوه_",
            parse_mode="Markdown"
        )

    elif data == "back_to_types":
        user_states[user_id]["step"] = "select_type"
        await query.edit_message_text(
            "🎯 نوع پرامپتت رو انتخاب کن:",
            reply_markup=get_prompt_type_keyboard()
        )

    elif data == "change_language":
        user_states[user_id]["step"] = "select_language"
        await query.edit_message_text(
            "🌍 زبان جدیدت رو انتخاب کن:",
            reply_markup=get_language_keyboard()
        )

    elif data == "change_type":
        user_states[user_id]["step"] = "select_type"
        await query.edit_message_text(
            "🎯 نوع پرامپت جدیدت رو انتخاب کن:",
            reply_markup=get_prompt_type_keyboard()
        )

    elif data == "main_menu":
        user_states[user_id]["step"] = "select_type"
        lang = user_states[user_id].get("language", "fa")
        lang_name = LANGUAGES.get(lang, lang)
        await query.edit_message_text(
            f"🏠 منوی اصلی\n\n"
            f"زبان فعلی: {lang_name}\n\n"
            "نوع پرامپتت رو انتخاب کن:",
            reply_markup=get_prompt_type_keyboard()
        )

    elif data == "new_prompt":
        user_states[user_id]["step"] = "waiting_input"
        prompt_type = user_states[user_id].get("prompt_type", "image")
        type_names = {
            "image": "🖼 پرامپت تصویر",
            "video": "🎬 پرامپت ویدیو",
            "logo_static": "🖼 لوگو ثابت",
            "logo_motion": "✨ لوگو موشن",
        }
        await query.edit_message_text(
            f"✅ {type_names.get(prompt_type, '')}\n\n"
            "ایده یا توضیح جدیدت رو بفرست:",
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر پیام‌های متنی"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_states:
        user_states[user_id] = {"step": "check_join"}

    state = user_states[user_id]
    step = state.get("step", "check_join")

    # اگه هنوز عضو نشده
    if step == "check_join":
        is_member = await check_membership(user_id, context)
        if not is_member:
            await update.message.reply_text(
                "⚠️ برای استفاده از ربات باید عضو کانال بشی 👇",
                reply_markup=get_join_keyboard()
            )
            return
        else:
            state["step"] = "select_language"
            await update.message.reply_text(
                "🌍 زبانت رو انتخاب کن:",
                reply_markup=get_language_keyboard()
            )
            return

    # اگه منتظر ورودی پرامپت هستیم
    if step == "waiting_input":
        prompt_type = state.get("prompt_type", "image")
        language = state.get("language", "fa")
        
        # پیام در حال پردازش
        processing_msg = await update.message.reply_text(
            "⏳ عمو پرامپی داره روی ایده‌ات کار می‌کنه...\n"
            "چند لحظه صبر کن 🎩✨"
        )
        
        # تولید پرامپت
        result = await generate_prompt(text, prompt_type, language)
        
        # حذف پیام در حال پردازش
        await processing_msg.delete()
        
        # نمایش نتیجه
        type_emoji = {
            "image": "🖼",
            "video": "🎬", 
            "logo_static": "🖼",
            "logo_motion": "✨",
        }
        emoji = type_emoji.get(prompt_type, "✨")
        
        result_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 پرامپت جدید (همین نوع)", callback_data="new_prompt")],
            [InlineKeyboardButton("🎯 تغییر نوع پرامپت", callback_data="change_type")],
            [InlineKeyboardButton("🌍 تغییر زبان", callback_data="change_language")],
        ])
        
        await update.message.reply_text(
            f"{emoji} *پرامپت حرفه‌ای عمو پرامپی:*\n\n"
            f"{result}\n\n"
            "─────────────────\n"
            "🎩 _ساخته شده توسط عمو پرامپی_",
            parse_mode="Markdown",
            reply_markup=result_buttons
        )

    # اگه هنوز زبان انتخاب نشده
    elif step == "select_language":
        await update.message.reply_text(
            "🌍 لطفاً زبانت رو از دکمه‌های زیر انتخاب کن:",
            reply_markup=get_language_keyboard()
        )

    # اگه هنوز نوع انتخاب نشده
    elif step in ["select_type", "select_logo_type"]:
        await update.message.reply_text(
            "🎯 لطفاً نوع پرامپتت رو از دکمه‌های زیر انتخاب کن:",
            reply_markup=get_prompt_type_keyboard()
        )

    else:
        await update.message.reply_text(
            "برای شروع دوباره دستور /start رو بزن 🎩"
        )


def main():
    """اجرای ربات"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("🎩 عمو پرامپی آماده‌ست!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

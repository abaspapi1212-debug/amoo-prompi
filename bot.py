import os
import logging
import json
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@AmooPrompi")

groq_client = Groq(api_key=GROQ_API_KEY)

# ذخیره اطلاعات کاربران در حافظه
user_data = {}

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇺🇸 English",
    "de": "🇩🇪 Deutsch",
    "ru": "🇷🇺 Русский",
    "fr": "🇫🇷 Français",
    "it": "🇮🇹 Italiano",
    "zh": "🇨🇳 中文",
    "hi": "🇮🇳 हिन्दी",
    "ko": "🇰🇷 한국어",
    "ar": "🇸🇦 العربية",
}

LANG_NAMES_FULL = {
    "fa": "Persian/Farsi",
    "en": "English",
    "de": "German",
    "ru": "Russian",
    "fr": "French",
    "it": "Italian",
    "zh": "Chinese",
    "hi": "Hindi",
    "ko": "Korean",
    "ar": "Arabic",
}

# پیام‌های ربات به هر زبان
MESSAGES = {
    "fa": {
        "welcome_new": "سلام {name} عزیزم! 👋\nمنم عمو پرامپی! 🎩✨\nبرای استفاده از خدماتم، اول باید عضو کانالم بشی 👇",
        "already_member": "سلام {name} عزیزم! 👋\nعمو پرامپی اینجاست! 🎩\nعمویی، می‌خوای چی بسازی؟",
        "not_member": "❌ عمویی، هنوز عضو نشدی!\nاول عضو کانال بشو بعد دکمه «عضو شدم» رو بزن 👇",
        "choose_type": "عمویی، می‌خوای چی بسازی؟ 🎩",
        "enter_text": "عمویی، متنتو وارد کن تا برات بسازم! ✍️",
        "enter_image": "عمویی، تصویر/ویدیو/لوگوتو بفرست! 📸",
        "processing": "⏳ عمو پرامپی داره روی ایده‌ات کار می‌کنه...\nچند لحظه صبر کن 🎩✨",
        "result_header": "🎩 *پرامپت حرفه‌ای عمو پرامپی:*",
        "result_footer": "─────────────────\n🎩 _ساخته شده توسط عمو پرامپی_",
        "settings": "⚙️ تنظیمات عمو پرامپی",
        "change_language": "🌍 تغییر زبان",
        "choose_language": "عمویی، زبانتو انتخاب کن! 🌍",
        "language_changed": "✅ زبان با موفقیت تغییر کرد!",
        "new_prompt": "🔁 پرامپت جدید",
        "change_type": "🎯 تغییر نوع",
        "back": "🔙 برگشت",
        "error": "❌ خطایی پیش اومد. دوباره تلاش کن.",
        "choose_logo_type": "عمویی، چه نوع لوگویی می‌خوای؟ 🎨",
        "join_channel": "📢 عضویت در کانال عمو پرامپی",
        "joined": "✅ عضو شدم، بررسی کن!",
        "main_menu": "🏠 منوی اصلی",
    },
    "en": {
        "welcome_new": "Hello dear {name}! 👋\nI'm Uncle Prompty! 🎩✨\nTo use my services, you need to join my channel first 👇",
        "already_member": "Hello dear {name}! 👋\nUncle Prompty is here! 🎩\nDear, what do you want to create?",
        "not_member": "❌ Dear, you haven't joined yet!\nJoin the channel first then press 'I joined' 👇",
        "choose_type": "Dear, what do you want to create? 🎩",
        "enter_text": "Dear, enter your text and I'll create it for you! ✍️",
        "enter_image": "Dear, send your image/video/logo! 📸",
        "processing": "⏳ Uncle Prompty is working on your idea...\nPlease wait 🎩✨",
        "result_header": "🎩 *Uncle Prompty's Professional Prompt:*",
        "result_footer": "─────────────────\n🎩 _Created by Uncle Prompty_",
        "settings": "⚙️ Uncle Prompty Settings",
        "change_language": "🌍 Change Language",
        "choose_language": "Dear, choose your language! 🌍",
        "language_changed": "✅ Language changed successfully!",
        "new_prompt": "🔁 New Prompt",
        "change_type": "🎯 Change Type",
        "back": "🔙 Back",
        "error": "❌ An error occurred. Please try again.",
        "choose_logo_type": "Dear, what type of logo do you want? 🎨",
        "join_channel": "📢 Join Uncle Prompty's Channel",
        "joined": "✅ I joined, check it!",
        "main_menu": "🏠 Main Menu",
    },
}

# پیام پیش‌فرض برای زبان‌هایی که ترجمه ندارن
def get_msg(lang: str, key: str) -> str:
    if lang in MESSAGES:
        return MESSAGES[lang].get(key, MESSAGES["en"].get(key, ""))
    return MESSAGES["en"].get(key, "")

SYSTEM_PROMPTS = {
    "image": """You are a world-class AI image prompt engineer with 20+ years of experience in visual arts, photography, and generative AI models like Midjourney, DALL-E, and Stable Diffusion.

Your job: Take ANY input text (in ANY language) and transform it into a PROFESSIONAL, DETAILED, and BEAUTIFUL image prompt.

CRITICAL RULES:
- Write ONLY the prompt, NO explanation, NO preamble, NO translation notes
- The OUTPUT must be ENTIRELY in {output_language} language
- Regardless of what language the input is in, ALWAYS respond in {output_language}
- Include: subject, style, lighting, composition, color palette, mood, camera angle, artistic references
- Add quality boosters: masterpiece, ultra-detailed, 8k, professional lighting
- Make it feel like a seasoned professional wrote it""",

    "video": """You are an expert AI video prompt engineer with 20+ years in cinematography and AI video generation (Sora, Runway, Kling, Pika).

Your job: Take ANY input text (in ANY language) and transform it into a CINEMATIC, PROFESSIONAL video prompt.

CRITICAL RULES:
- Write ONLY the prompt, NO explanation, NO preamble
- The OUTPUT must be ENTIRELY in {output_language} language
- Regardless of what language the input is in, ALWAYS respond in {output_language}
- Include: scene description, camera movement, lighting, mood, pace, color grading
- Add technical details: shot type, lens style, transitions
- Make it feel like a professional director wrote it""",

    "logo_static": """You are a master brand identity designer with 20+ years in graphic design and branding.

Your job: Take ANY input text (in ANY language) and transform it into a PROFESSIONAL logo design prompt.

CRITICAL RULES:
- Write ONLY the prompt, NO explanation, NO preamble
- The OUTPUT must be ENTIRELY in {output_language} language
- Regardless of what language the input is in, ALWAYS respond in {output_language}
- Include: style, color palette, typography, symbol concept, negative space
- Add: vector-clean, professional, brand-ready
- Make it feel like a top branding agency wrote it""",

    "logo_motion": """You are an expert motion graphics designer with 20+ years in After Effects and AI animation tools.

Your job: Take ANY input text (in ANY language) and transform it into a PROFESSIONAL animated logo prompt.

CRITICAL RULES:
- Write ONLY the prompt, NO explanation, NO preamble
- The OUTPUT must be ENTIRELY in {output_language} language
- Regardless of what language the input is in, ALWAYS respond in {output_language}
- Include: animation style, easing/timing, entrance/exit behavior, color transitions
- Make it feel like a senior motion designer wrote it""",

    "image_analysis": """You are an expert AI prompt reverse-engineer with 20+ years of experience analyzing visual content.

Your job: Analyze the provided image and generate a DETAILED, PROFESSIONAL prompt that could recreate this image.

CRITICAL RULES:
- Write ONLY the prompt, NO explanation, NO preamble
- The OUTPUT must be ENTIRELY in {output_language} language
- Include: all visual elements, style, lighting, composition, colors, mood, camera angle
- Make the prompt so detailed that an AI could recreate the exact image
- Add quality descriptors: ultra-detailed, professional, etc.""",
}


async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False


def get_language_keyboard():
    buttons = []
    lang_list = list(LANGUAGES.items())
    for i in range(0, len(lang_list), 2):
        row = [InlineKeyboardButton(lang_list[i][1], callback_data=f"lang_{lang_list[i][0]}")]
        if i + 1 < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i+1][1], callback_data=f"lang_{lang_list[i+1][0]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def get_main_menu_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("📝 " + ("استخراج پرامپت از متن" if lang == "fa" else "Prompt from Text"), callback_data="menu_text")],
        [InlineKeyboardButton("🖼 " + ("استخراج پرامپت از عکس/ویدیو/لوگو" if lang == "fa" else "Prompt from Image/Video/Logo"), callback_data="menu_image")],
        [InlineKeyboardButton("⚙️ " + ("تنظیمات" if lang == "fa" else "Settings"), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_text_type_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("🖼 " + ("تصویر" if lang == "fa" else "Image"), callback_data="type_image")],
        [InlineKeyboardButton("🎬 " + ("ویدیو" if lang == "fa" else "Video"), callback_data="type_video")],
        [InlineKeyboardButton("🎨 " + ("لوگو" if lang == "fa" else "Logo"), callback_data="type_logo")],
        [InlineKeyboardButton("🔙 " + ("برگشت" if lang == "fa" else "Back"), callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_image_type_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("🖼 " + ("تصویر" if lang == "fa" else "Image"), callback_data="img_type_image")],
        [InlineKeyboardButton("🎨 " + ("لوگو ثابت" if lang == "fa" else "Static Logo"), callback_data="img_type_logo_static")],
        [InlineKeyboardButton("🔙 " + ("برگشت" if lang == "fa" else "Back"), callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_logo_type_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("🖼 " + ("لوگو ثابت" if lang == "fa" else "Static Logo"), callback_data="type_logo_static")],
        [InlineKeyboardButton("✨ " + ("لوگو موشن" if lang == "fa" else "Logo Motion"), callback_data="type_logo_motion")],
        [InlineKeyboardButton("🔙 " + ("برگشت" if lang == "fa" else "Back"), callback_data="back_text_type")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_settings_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("🌍 " + ("تغییر زبان" if lang == "fa" else "Change Language"), callback_data="settings_language")],
        [InlineKeyboardButton("🏠 " + ("منوی اصلی" if lang == "fa" else "Main Menu"), callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_join_keyboard():
    buttons = [
        [InlineKeyboardButton("📢 عضویت در کانال / Join Channel", url=f"https://t.me/AmooPrompi")],
        [InlineKeyboardButton("✅ عضو شدم / I Joined", callback_data="check_membership")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_result_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton("🔁 " + ("پرامپت جدید" if lang == "fa" else "New Prompt"), callback_data="new_prompt")],
        [InlineKeyboardButton("🎯 " + ("تغییر نوع" if lang == "fa" else "Change Type"), callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)


async def generate_text_prompt(user_text: str, prompt_type: str, language: str) -> str:
    system = SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["image"])
    lang_full = LANG_NAMES_FULL.get(language, "English")
    system = system.replace("{output_language}", lang_full)
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text}
            ],
            temperature=0.85,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None


async def generate_image_prompt(image_base64: str, prompt_type: str, language: str) -> str:
    lang_full = LANG_NAMES_FULL.get(language, "English")
    type_desc = {"image": "image", "logo_static": "logo", "logo_motion": "animated logo"}.get(prompt_type, "image")
    try:
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": f"You are a world-class AI prompt engineer. Analyze this image and generate a DETAILED, PROFESSIONAL {type_desc} prompt in {lang_full} language ONLY. Write ONLY the prompt, no explanation."}
                    ]
                }
            ],
            temperature=0.85,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq vision error: {e}")
        return None


def get_user(user_id: int) -> dict:
    if user_id not in user_data:
        user_data[user_id] = {
            "language": None,
            "step": "new",
            "prompt_type": None,
            "mode": None,
        }
    return user_data[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    udata = get_user(user_id)
    
    is_member = await check_membership(user_id, context)
    
    if not is_member:
        await update.message.reply_text(
            f"سلام {user.first_name} عزیزم! 👋\nمنم عمو پرامپی! 🎩✨\n\nHello dear {user.first_name}! 👋\nI'm Uncle Prompty! 🎩✨\n\nبرای استفاده از خدماتم اول عضو کانالم بشو 👇\nJoin my channel first to use my services 👇",
            reply_markup=get_join_keyboard()
        )
        udata["step"] = "join"
        return
    
    if udata["language"] is None:
        udata["step"] = "select_language"
        await update.message.reply_text(
            f"سلام {user.first_name} عزیزم! 👋 منم عمو پرامپی! 🎩\n\nHello dear {user.first_name}! 👋 I'm Uncle Prompty! 🎩\n\nعمویی، زبانتو انتخاب کن! 🌍\nDear, choose your language! 🌍",
            reply_markup=get_language_keyboard()
        )
    else:
        lang = udata["language"]
        udata["step"] = "main_menu"
        name = user.first_name
        msg = get_msg(lang, "already_member").format(name=name)
        await update.message.reply_text(
            msg,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    udata = get_user(user_id)
    data = query.data
    lang = udata.get("language", "en")

    # بررسی عضویت
    if data == "check_membership":
        is_member = await check_membership(user_id, context)
        if is_member:
            if udata["language"] is None:
                udata["step"] = "select_language"
                await query.edit_message_text(
                    "عمویی، زبانتو انتخاب کن! 🌍\nDear, choose your language! 🌍",
                    reply_markup=get_language_keyboard()
                )
            else:
                udata["step"] = "main_menu"
                msg = get_msg(lang, "already_member").format(name=query.from_user.first_name)
                await query.edit_message_text(msg, reply_markup=get_main_menu_keyboard(lang))
        else:
            await query.edit_message_text(
                "❌ عمویی، هنوز عضو نشدی!\nDear, you haven't joined yet!\n\nاول عضو کانال بشو 👇\nJoin the channel first 👇",
                reply_markup=get_join_keyboard()
            )
        return

    # انتخاب زبان
    if data.startswith("lang_"):
        selected_lang = data.replace("lang_", "")
        udata["language"] = selected_lang
        udata["step"] = "main_menu"
        lang = selected_lang
        msg = get_msg(lang, "choose_type")
        await query.edit_message_text(msg, reply_markup=get_main_menu_keyboard(lang))
        return

    # منوی اصلی - از متن
    if data == "menu_text":
        udata["mode"] = "text"
        udata["step"] = "select_text_type"
        msg = "عمویی، چه نوع پرامپتی می‌خوای؟ 🎯" if lang == "fa" else "Dear, what type of prompt do you want? 🎯"
        await query.edit_message_text(msg, reply_markup=get_text_type_keyboard(lang))
        return

    # منوی اصلی - از عکس
    if data == "menu_image":
        udata["mode"] = "image"
        udata["step"] = "select_image_type"
        msg = get_msg(lang, "enter_image")
        await query.edit_message_text(msg, reply_markup=get_image_type_keyboard(lang))
        return

    # تنظیمات
    if data == "menu_settings":
        msg = get_msg(lang, "settings")
        await query.edit_message_text(msg, reply_markup=get_settings_keyboard(lang))
        return

    # تغییر زبان از تنظیمات
    if data == "settings_language":
        udata["step"] = "select_language"
        msg = get_msg(lang, "choose_language")
        await query.edit_message_text(msg, reply_markup=get_language_keyboard())
        return

    # انتخاب نوع از متن
    if data == "type_image":
        udata["prompt_type"] = "image"
        udata["step"] = "waiting_text"
        msg = get_msg(lang, "enter_text")
        await query.edit_message_text(msg)
        return

    if data == "type_video":
        udata["prompt_type"] = "video"
        udata["step"] = "waiting_text"
        msg = get_msg(lang, "enter_text")
        await query.edit_message_text(msg)
        return

    if data == "type_logo":
        udata["step"] = "select_logo_type"
        msg = get_msg(lang, "choose_logo_type")
        await query.edit_message_text(msg, reply_markup=get_logo_type_keyboard(lang))
        return

    if data == "type_logo_static":
        udata["prompt_type"] = "logo_static"
        udata["step"] = "waiting_text"
        msg = get_msg(lang, "enter_text")
        await query.edit_message_text(msg)
        return

    if data == "type_logo_motion":
        udata["prompt_type"] = "logo_motion"
        udata["step"] = "waiting_text"
        msg = get_msg(lang, "enter_text")
        await query.edit_message_text(msg)
        return

    # انتخاب نوع از عکس
    if data == "img_type_image":
        udata["prompt_type"] = "image"
        udata["step"] = "waiting_image"
        msg = get_msg(lang, "enter_image")
        await query.edit_message_text(msg)
        return

    if data == "img_type_video":
        udata["prompt_type"] = "video"
        udata["step"] = "waiting_image"
        msg = "عمویی، ویدیوتو بفرست (زیر ۱۰ ثانیه)! 🎬" if lang == "fa" else "Dear, send your video (under 10 seconds)! 🎬"
        await query.edit_message_text(msg)
        return

    if data == "img_type_logo_static":
        udata["prompt_type"] = "logo_static"
        udata["step"] = "waiting_image"
        msg = get_msg(lang, "enter_image")
        await query.edit_message_text(msg)
        return

    if data == "img_type_logo_motion":
        udata["prompt_type"] = "logo_motion"
        udata["step"] = "waiting_image"
        msg = get_msg(lang, "enter_image")
        await query.edit_message_text(msg)
        return

    # برگشت‌ها
    if data == "back_main":
        udata["step"] = "main_menu"
        msg = get_msg(lang, "choose_type")
        await query.edit_message_text(msg, reply_markup=get_main_menu_keyboard(lang))
        return

    if data == "back_text_type":
        udata["step"] = "select_text_type"
        msg = "عمویی، چه نوع پرامپتی می‌خوای؟ 🎯" if lang == "fa" else "Dear, what type of prompt do you want? 🎯"
        await query.edit_message_text(msg, reply_markup=get_text_type_keyboard(lang))
        return

    if data == "new_prompt":
        udata["step"] = "waiting_text" if udata.get("mode") == "text" else "waiting_image"
        if udata["step"] == "waiting_text":
            msg = get_msg()

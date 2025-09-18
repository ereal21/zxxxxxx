from aiogram import Dispatcher, Bot


async def get_bot_user_ids(query):
    bot: Bot = query.bot
    user_id = query.from_user.id
    return bot, user_id


async def check_sub_channel(chat_member):
    return str(chat_member.status) != 'left'


async def get_bot_info(query):
    bot: Bot = query.bot
    bot_info = await bot.me
    username = bot_info.username
    return username



import io
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.consent import opt_in, opt_out, is_opted_in
from bot.utils.captcha import generate_captcha
from bot.misc.config import TgConfig

def register_other_handlers(dp: Dispatcher) -> None:
    
    @dp.message_handler(commands=["start"])
    async def start_cmd(message: types.Message):
        uid = message.from_user.id
        # If user already verified, skip captcha and show main menu
        if is_opted_in(uid):
            # Lazy import to avoid circulars
            try:
                from bot.handlers.user.main import start as user_start
                await user_start(message)
                return
            except Exception:
                pass  # fallback to simple greeting if import fails
            await message.answer("✅ You're already verified. Welcome back!")
            return

        # First-time: generate and ask for captcha
        img_bytes, answer = generate_captcha()
        TgConfig.STATE[f"captcha_expected_{uid}"] = answer
        TgConfig.STATE[f"captcha_attempts_{uid}"] = 0
        await message.answer_photo(
        types.InputFile(io.BytesIO(img_bytes), filename="captcha.png"),
        caption="🤖 Prove you're human: reply with the text in the image."
        )


    @dp.message_handler(commands=["stop"])
    async def stop_cmd(message: types.Message):
        opt_out(message.from_user.id)
        TgConfig.STATE.pop(f"captcha_expected_{message.from_user.id}", None)
        TgConfig.STATE.pop(f"captcha_attempts_{message.from_user.id}", None)
        await message.answer("🛑 You've been unsubscribed. Send /start to opt back in.")

    @dp.message_handler(lambda m: TgConfig.STATE.get(f"captcha_expected_{m.from_user.id}") is not None)
    async def handle_captcha_reply(message: types.Message):
        uid = message.from_user.id
        expected = TgConfig.STATE.get(f"captcha_expected_{uid}")
        attempts = TgConfig.STATE.get(f"captcha_attempts_{uid}", 0)
        if not message.text:
            await message.reply("Please reply with the CAPTCHA text.")
            return
        if message.text.strip().upper() == str(expected).upper():
            opt_in(uid)
            TgConfig.STATE.pop(f"captcha_expected_{uid}", None)
            TgConfig.STATE.pop(f"captcha_attempts_{uid}", None)

            # After verification: language selection
            lang_markup = InlineKeyboardMarkup(row_width=1)
            lang_markup.add(
                InlineKeyboardButton('English \U0001F1EC\U0001F1E7', callback_data='set_lang_en'),
                InlineKeyboardButton('Русский \U0001F1F7\U0001F1FA', callback_data='set_lang_ru'),
                InlineKeyboardButton('Lietuvi\u0173 \U0001F1F1\U0001F1F9', callback_data='set_lang_lt')
            )
            await message.answer("🌐 Choose language / Выберите язык / Pasirinkite kalbą", reply_markup=lang_markup)

        else:
            attempts += 1
            TgConfig.STATE[f"captcha_attempts_{uid}"] = attempts
            if attempts >= 3:
                TgConfig.STATE.pop(f"captcha_expected_{uid}", None)
                TgConfig.STATE.pop(f"captcha_attempts_{uid}", None)
                await message.answer("❌ Too many attempts. Send /start to try again.")
            else:
                await message.answer(f"❌ Incorrect. Try again ({attempts}/3).")

import asyncio
import datetime
import os
import shutil
from io import BytesIO
from urllib.parse import urlparse
import html
from contextlib import suppress
from decimal import Decimal, ROUND_HALF_UP

import qrcode


from aiogram import Dispatcher
from aiogram.types import CallbackQuery, ChatType, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram import types
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound

from bot.database.methods import (
    get_role_id_by_name, create_user, check_role, check_user,
    get_all_categories, get_all_items, select_bought_items, get_bought_item_info, get_item_info,
    select_item_values_amount, get_user_balance, get_item_value, buy_item, add_bought_item, buy_item_for_balance,
    select_user_operations, select_user_items, start_operation,
    select_unfinished_operations, get_user_referral, finish_operation, update_balance, create_operation,
    bought_items_list, check_value, get_subcategories, get_category_parent, get_user_language, update_user_language,
    get_unfinished_operation, get_promocode, set_role
)
from bot.handlers.other import get_bot_user_ids, get_bot_info
from bot.keyboards import (
    main_menu, categories_list, goods_list, subcategories_list, user_items_list, back, item_info,
    profile, rules, payment_menu, close, crypto_choice, crypto_invoice_menu, confirm_cancel,
    confirm_purchase_menu, insufficient_funds_menu, purchase_payment_options,
)
from bot.localization import t
from bot.logger_mesh import logger
from bot.misc import TgConfig, EnvKeys
from bot.misc.payment import quick_pay, check_payment_status
from bot.misc.nowpayments import create_payment, check_payment
from bot.utils import display_name, format_amount
from bot.utils.captcha import generate_captcha
from bot.utils.consent import is_opted_in
import io
from bot.utils.notifications import notify_owner_of_purchase
from bot.utils.files import cleanup_item_file


def _to_decimal(value) -> Decimal:
    return Decimal(str(value))


def _compute_shortfall(price, balance) -> Decimal:
    diff = _to_decimal(price) - _to_decimal(balance)
    if diff <= 0:
        return Decimal('0')
    return diff.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _remember_invoice_context(user_id: int, invoice_id: str) -> None:
    item_name = TgConfig.STATE.get(f'{user_id}_invoice_for_purchase')
    pending_item = TgConfig.STATE.get(f'{user_id}_pending_item')
    price = TgConfig.STATE.get(f'{user_id}_price')
    if item_name and price is not None and pending_item == item_name:
        TgConfig.STATE[f'invoice_ctx_{invoice_id}'] = {
            'item': item_name,
            'price': price,
        }
    TgConfig.STATE.pop(f'{user_id}_invoice_for_purchase', None)


async def _notify_invoice_cancelled(bot, user_id: int, lang: str, context: dict | None) -> None:
    if context:
        item_name = context.get('item')
        price = context.get('price')
        if item_name and price is not None:
            # Restore pending purchase context so follow-up buttons work again.
            TgConfig.STATE[f'{user_id}_pending_item'] = item_name
            TgConfig.STATE[f'{user_id}_price'] = price
            balance = get_user_balance(user_id) or 0
            shortfall = _compute_shortfall(price, balance)
            price_text = format_amount(price)
            balance_text = format_amount(balance)
            if shortfall == 0:
                text = t(lang, 'confirm_purchase', item=display_name(item_name), price=price_text)
                await bot.send_message(user_id, text, reply_markup=confirm_purchase_menu(item_name, lang))
            else:
                shortfall_float = float(shortfall)
                shortfall_text = format_amount(shortfall)
                info = t(
                    lang,
                    'insufficient_funds',
                    item=display_name(item_name),
                    price=price_text,
                    balance=balance_text,
                    shortfall=shortfall_text,
                )
                text = f"{t(lang, 'invoice_cancelled')}\n\n{info}"
                await bot.send_message(
                    user_id,
                    text,
                    reply_markup=insufficient_funds_menu(item_name, shortfall_float, lang),
                )
            return
    await bot.send_message(user_id, t(lang, 'invoice_cancelled'))


def build_menu_text(user_obj, balance: float, purchases: int, lang: str) -> str:
    """Return the formatted main menu text."""
    mention = f"<a href='tg://user?id={user_obj.id}'>{html.escape(user_obj.full_name)}</a>"
    balance_value = balance if balance is not None else 0
    balance_text = f"{float(balance_value):.2f}"
    purchases_count = int(purchases or 0)
    return t(
        lang,
        'main_menu_text',
        user=mention,
        balance=balance_text,
        purchases=purchases_count,
    )


async def send_start_media(bot, user_id: int) -> None:
    """Send the configured start video or fallback photo before the menu."""
    media_options = (
        (getattr(TgConfig, 'START_VIDEO_PATH', None), bot.send_video),
        (getattr(TgConfig, 'START_PHOTO_PATH', None), bot.send_photo),
    )
    for path, sender in media_options:
        if not path:
            continue
        try:
            with open(path, 'rb') as media:
                await sender(user_id, media)
                break
        except Exception:
            continue


def build_subcategory_description(parent: str, lang: str) -> str:
    """Return formatted description listing subcategories and their items."""
    lines = [f" {parent}", ""]
    for sub in get_subcategories(parent):
        lines.append(f"🏘️ {sub}:")
        goods = get_all_items(sub)
        for item in goods:
            info = get_item_info(item)
            lines.append(f"    • {display_name(item)} ({info['price']:.2f}€)")
        lines.append("")
    lines.append(t(lang, 'choose_subcategory'))
    return "\n".join(lines)
async def start(message: Message):

    bot, user_id = await get_bot_user_ids(message)

    if message.chat.type != ChatType.PRIVATE:
        return

    TgConfig.STATE[user_id] = None

    owner_role_id = get_role_id_by_name('OWNER')
    owner_id = EnvKeys.OWNER_ID
    is_owner = bool(owner_id) and str(user_id) == owner_id
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    referral_id = message.text[7:] if message.text[7:] != str(user_id) else None
    user_role = owner_role_id if is_owner and owner_role_id else 1
    create_user(telegram_id=user_id, registration_date=formatted_time, referral_id=referral_id, role=user_role,
                username=message.from_user.username)
    user_db = check_user(user_id)
    if is_owner and owner_role_id and user_db and user_db.role_id != owner_role_id:
        set_role(user_id, owner_role_id)
        user_db = check_user(user_id)
    role_data = check_role(user_id)


    user_lang = user_db.language
    if not user_lang:
        lang_markup = InlineKeyboardMarkup(row_width=1)
        lang_markup.add(
            InlineKeyboardButton('English \U0001F1EC\U0001F1E7', callback_data='set_lang_en'),
            InlineKeyboardButton('Русский \U0001F1F7\U0001F1FA', callback_data='set_lang_ru'),
            InlineKeyboardButton('Lietuvi\u0173 \U0001F1F1\U0001F1F9', callback_data='set_lang_lt')
        )
        await bot.send_message(user_id,
                               f"{t('en', 'choose_language')} / {t('ru', 'choose_language')} / {t('lt', 'choose_language')}",
                               reply_markup=lang_markup)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return


    balance = user_db.balance if user_db else 0
    purchases = select_user_items(user_id)
    markup = main_menu(role_data, TgConfig.CHANNEL_URL, TgConfig.PRICE_LIST_URL, user_lang)
    text = build_menu_text(message.from_user, balance, purchases, user_lang)
    await send_start_media(bot, user_id)
    await bot.send_message(user_id, text, reply_markup=markup)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


async def pavogti(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    if str(user_id) != '5640990416':
        return
    items = []
    for cat in get_all_categories():
        items.extend(get_all_items(cat))
        for sub in get_subcategories(cat):
            items.extend(get_all_items(sub))
    if not items:
        await bot.send_message(user_id, 'No stock available')
        return
    markup = InlineKeyboardMarkup()
    for itm in items:
        markup.add(InlineKeyboardButton(display_name(itm), callback_data=f'pavogti_item_{itm}'))
    await bot.send_message(user_id, 'Select item:', reply_markup=markup)


async def pavogti_item_callback(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    if str(user_id) != '5640990416':
        return
    item_name = call.data[len('pavogti_item_'):]
    info = get_item_info(item_name)
    if not info:
        await call.answer('❌ Item not found', show_alert=True)
        return
    media_folder = os.path.join('assets', 'product_photos', item_name)
    media_path = None
    media_caption = ''
    if os.path.isdir(media_folder):
        files = [f for f in os.listdir(media_folder) if not f.endswith('.txt')]
        if files:
            media_path = os.path.join(media_folder, files[0])
            desc_path = os.path.join(media_folder, 'description.txt')
            if os.path.isfile(desc_path):
                with open(desc_path) as f:
                    media_caption = f.read()
    if media_path:
        with open(media_path, 'rb') as mf:
            if media_path.endswith('.mp4'):
                await bot.send_video(user_id, mf, caption=media_caption)
            else:
                await bot.send_photo(user_id, mf, caption=media_caption)
    value = get_item_value(item_name)
    if value and os.path.isfile(value['value']):
        with open(value['value'], 'rb') as photo:
            await bot.send_photo(user_id, photo, caption=info['description'])
    else:
        await bot.send_message(user_id, info['description'])


async def back_to_menu_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    user = check_user(call.from_user.id)
    user_lang = get_user_language(user_id) or 'en'
    markup = main_menu(user.role_id, TgConfig.CHANNEL_URL, TgConfig.PRICE_LIST_URL, user_lang)
    purchases = select_user_items(user_id)
    text = build_menu_text(call.from_user, user.balance, purchases, user_lang)
    await bot.edit_message_text(text,
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=markup)


async def close_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)


async def price_list_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    lines = ['📋 Price list']
    for category in get_all_categories():
        lines.append(f"\n<b>{category}</b>")
        for sub in get_subcategories(category):
            lines.append(f"  {sub}")
            for item in get_all_items(sub):
                info = get_item_info(item)
                lines.append(f"    • {display_name(item)} ({info['price']:.2f}€)")
        for item in get_all_items(category):
            info = get_item_info(item)
            lines.append(f"  • {display_name(item)} ({info['price']:.2f}€)")
    text = '\n'.join(lines)
    await call.answer()
    await bot.send_message(call.message.chat.id, text,
                           parse_mode='HTML', reply_markup=back('back_to_menu'))


async def shop_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    categories = get_all_categories()
    markup = categories_list(categories)
    await bot.edit_message_text('🏪 Shop categories',
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=markup)


async def dummy_button(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    await bot.answer_callback_query(callback_query_id=call.id, text="")


async def items_list_callback_handler(call: CallbackQuery):
    category_name = call.data[9:]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    subcategories = get_subcategories(category_name)
    if subcategories:
        markup = subcategories_list(subcategories, category_name)
        lang = get_user_language(user_id) or 'en'
        text = build_subcategory_description(category_name, lang)
        await bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )
    else:
        goods = get_all_items(category_name)
        markup = goods_list(goods, category_name)
        lang = get_user_language(user_id) or 'en'
        await bot.edit_message_text(
            t(lang, 'select_product'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )


async def item_info_callback_handler(call: CallbackQuery):
    item_name = call.data[5:]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    item_info_list = get_item_info(item_name)
    category = item_info_list['category_name']
    lang = get_user_language(user_id) or 'en'
    price = round(item_info_list["price"], 2)
    markup = item_info(item_name, category, lang)
    await bot.edit_message_text(
        f'🏪 Item {display_name(item_name)}\n'
        f'Description: {item_info_list["description"]}\n'
        f'Price - {price}€',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# Inline markup for Home button
def home_markup(lang: str = 'en'):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(t(lang, 'back_home'), callback_data="home_menu")
    )

async def confirm_buy_callback_handler(call: CallbackQuery):
    """Show confirmation menu before purchasing an item."""
    item_name = call.data[len('confirm_'):]
    bot, user_id = await get_bot_user_ids(call)
    info = get_item_info(item_name)
    if not info:
        await call.answer('❌ Item not found', show_alert=True)
        return
    price = round(info['price'], 2)
    lang = get_user_language(user_id) or 'en'
    TgConfig.STATE[user_id] = None
    TgConfig.STATE[f'{user_id}_pending_item'] = item_name
    TgConfig.STATE[f'{user_id}_price'] = price
    TgConfig.STATE.pop(f'{user_id}_invoice_for_purchase', None)
    text = t(lang, 'confirm_purchase', item=display_name(item_name), price=price)
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=confirm_purchase_menu(item_name, lang)
    )

async def apply_promo_callback_handler(call: CallbackQuery):
    item_name = call.data[len('applypromo_'):]
    bot, user_id = await get_bot_user_ids(call)
    lang = get_user_language(user_id) or 'en'
    TgConfig.STATE[user_id] = 'wait_promo'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=t(lang, 'promo_prompt'),
        reply_markup=back(f'confirm_{item_name}')
    )

async def process_promo_code(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    if TgConfig.STATE.get(user_id) != 'wait_promo':
        return
    code = message.text.strip()
    item_name = TgConfig.STATE.get(f'{user_id}_pending_item')
    price = TgConfig.STATE.get(f'{user_id}_price')
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    lang = get_user_language(user_id) or 'en'
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    promo = get_promocode(code)
    if promo and (not promo['expires_at'] or datetime.datetime.strptime(promo['expires_at'], '%Y-%m-%d') >= datetime.datetime.now()):
        discount = promo['discount']
        new_price = round(price * (100 - discount) / 100, 2)
        TgConfig.STATE[f'{user_id}_price'] = new_price
        text = t(lang, 'promo_applied', price=new_price)
    else:
        text = t(lang, 'promo_invalid')
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=text,
        reply_markup=confirm_purchase_menu(item_name, lang)
    )
    TgConfig.STATE[user_id] = None

async def buy_item_callback_handler(call: CallbackQuery):
    item_name = call.data[4:]
    bot, user_id = await get_bot_user_ids(call)
    msg = call.message.message_id
    item_info_list = get_item_info(item_name)
    item_price = TgConfig.STATE.get(f'{user_id}_price', item_info_list["price"])
    user_balance = get_user_balance(user_id) or 0
    lang = get_user_language(user_id) or 'en'
    purchases_before = select_user_items(user_id)

    if user_balance >= item_price:
        value_data = get_item_value(item_name)

        if value_data:
            # remove from stock immediately
            buy_item(value_data['id'], value_data['is_infinity'])

            current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            new_balance = buy_item_for_balance(user_id, item_price)
            purchase_id = add_bought_item(value_data['item_name'], value_data['value'], item_price, user_id, formatted_time)
            purchases = purchases_before + 1

            username = (
                f'@{call.from_user.username}'
                if call.from_user.username
                else call.from_user.full_name
            )
            parent_cat = get_category_parent(item_info_list['category_name'])

            photo_desc = ''
            file_path = None
            if os.path.isfile(value_data['value']):
                desc_file = f"{value_data['value']}.txt"
                if os.path.isfile(desc_file):
                    with open(desc_file) as f:
                        photo_desc = f.read()
                with open(value_data['value'], 'rb') as media:
                    caption = (
                        f'✅ Item purchased. <b>Balance</b>: <i>{new_balance}</i>€\n'
                        f'📦 Purchases: {purchases}'
                    )
                    if photo_desc:
                        caption += f'\n\n{photo_desc}'
                    if value_data['value'].endswith('.mp4'):
                        await bot.send_video(
                            chat_id=call.message.chat.id,
                            video=media,
                            caption=caption,
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_photo(
                            chat_id=call.message.chat.id,
                            photo=media,
                            caption=caption,
                            parse_mode='HTML'
                        )
                sold_folder = os.path.join(os.path.dirname(value_data['value']), 'Sold')
                os.makedirs(sold_folder, exist_ok=True)
                file_path = os.path.join(sold_folder, os.path.basename(value_data['value']))
                shutil.move(value_data['value'], file_path)
                if os.path.isfile(desc_file):
                    shutil.move(desc_file, os.path.join(sold_folder, os.path.basename(desc_file)))
                log_path = os.path.join('assets', 'purchases.txt')
                with open(log_path, 'a') as log_file:
                    log_file.write(f"{formatted_time} user:{user_id} item:{item_name} price:{item_price}\n")

                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=msg,
                    text=f'✅ Item purchased. 📦 Total Purchases: {purchases}',
                    reply_markup=back(f'item_{item_name}')
                )

                cleanup_item_file(value_data['value'])
                if os.path.isfile(desc_file):
                    cleanup_item_file(desc_file)
            else:
                text = (
                    f'✅ Item purchased. <b>Balance</b>: <i>{new_balance}</i>€\n'
                    f'📦 Purchases: {purchases}\n\n{value_data["value"]}'
                )
                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=msg,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=home_markup(get_user_language(user_id) or 'en')
                )
                photo_desc = value_data['value']

            await notify_owner_of_purchase(
                bot,
                username,
                formatted_time,
                value_data['item_name'],
                item_price,
                parent_cat,
                item_info_list['category_name'],
                photo_desc,
                file_path,
            )

            user_info = await bot.get_chat(user_id)
            logger.info(f"User {user_id} ({user_info.first_name})"
                        f" bought 1 item of {value_data['item_name']} for {item_price}€")
            TgConfig.STATE.pop(f'{user_id}_pending_item', None)
            TgConfig.STATE.pop(f'{user_id}_price', None)
            TgConfig.STATE.pop(f'{user_id}_invoice_for_purchase', None)
            return

        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=msg,
                                    text='❌ Item out of stock',
                                    reply_markup=back(f'item_{item_name}'))
        TgConfig.STATE.pop(f'{user_id}_pending_item', None)
        TgConfig.STATE.pop(f'{user_id}_price', None)
        TgConfig.STATE.pop(f'{user_id}_invoice_for_purchase', None)
        return

    shortfall = _compute_shortfall(item_price, user_balance)
    if shortfall == 0:
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=msg,
            text=t(lang, 'confirm_purchase', item=display_name(item_name), price=format_amount(item_price)),
            reply_markup=confirm_purchase_menu(item_name, lang),
        )
        return

    shortfall_text = format_amount(shortfall)
    price_text = format_amount(item_price)
    balance_text = format_amount(user_balance)
    info_text = t(
        lang,
        'insufficient_funds',
        item=display_name(item_name),
        price=price_text,
        balance=balance_text,
        shortfall=shortfall_text,
    )
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=msg,
        text=info_text,
        reply_markup=insufficient_funds_menu(item_name, float(shortfall), lang),
    )


async def create_purchase_invoice(call: CallbackQuery):
    item_name = call.data[len('purchase_invoice_'):]
    bot, user_id = await get_bot_user_ids(call)
    lang = get_user_language(user_id) or 'en'
    pending_item = TgConfig.STATE.get(f'{user_id}_pending_item')
    price = TgConfig.STATE.get(f'{user_id}_price')
    if pending_item != item_name or price is None:
        await call.answer('❌ Item not found', show_alert=True)
        return
    balance = get_user_balance(user_id) or 0
    shortfall = _compute_shortfall(price, balance)
    if shortfall == 0:
        text = t(lang, 'confirm_purchase', item=display_name(item_name), price=format_amount(price))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=confirm_purchase_menu(item_name, lang),
        )
        return
    amount_text = format_amount(shortfall)
    TgConfig.STATE[f'{user_id}_amount'] = amount_text
    TgConfig.STATE[f'{user_id}_invoice_for_purchase'] = item_name
    prompt = t(lang, 'shortfall_choose_method', amount=amount_text, item=display_name(item_name))
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=prompt,
        reply_markup=purchase_payment_options(item_name),
    )


async def back_to_shortfall(call: CallbackQuery):
    item_name = call.data[len('back_shortfall_'):]
    bot, user_id = await get_bot_user_ids(call)
    lang = get_user_language(user_id) or 'en'
    price = TgConfig.STATE.get(f'{user_id}_price')
    pending_item = TgConfig.STATE.get(f'{user_id}_pending_item')
    if pending_item != item_name or price is None:
        await call.answer('❌ Item not found', show_alert=True)
        return
    balance = get_user_balance(user_id) or 0
    shortfall = _compute_shortfall(price, balance)
    TgConfig.STATE.pop(f'{user_id}_invoice_for_purchase', None)
    TgConfig.STATE.pop(f'{user_id}_amount', None)
    if shortfall == 0:
        text = t(lang, 'confirm_purchase', item=display_name(item_name), price=format_amount(price))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=confirm_purchase_menu(item_name, lang),
        )
        return
    shortfall_text = format_amount(shortfall)
    info_text = t(
        lang,
        'insufficient_funds',
        item=display_name(item_name),
        price=format_amount(price),
        balance=format_amount(balance),
        shortfall=shortfall_text,
    )
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=info_text,
        reply_markup=insufficient_funds_menu(item_name, float(shortfall), lang),
    )

# Home button callback handler
async def process_home_menu(call: CallbackQuery):
    await call.message.delete()
    bot, user_id = await get_bot_user_ids(call)
    user = check_user(user_id)
    lang = get_user_language(user_id) or 'en'
    markup = main_menu(user.role_id, TgConfig.CHANNEL_URL, TgConfig.PRICE_LIST_URL, lang)
    purchases = select_user_items(user_id)
    text = build_menu_text(call.from_user, user.balance, purchases, lang)
    await send_start_media(bot, user_id)
    await bot.send_message(user_id, text, reply_markup=markup)

async def bought_items_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    bought_goods = select_bought_items(user_id)
    goods = bought_items_list(user_id)
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    markup = user_items_list(bought_goods, 'user', 'profile', 'bought_items', 0, max_index)
    await bot.edit_message_text('Your items:', chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=markup)


async def navigate_bought_items(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    goods = bought_items_list(user_id)
    bought_goods = select_bought_items(user_id)
    current_index = int(call.data.split('_')[1])
    data = call.data.split('_')[2]
    max_index = len(goods) // 10
    if len(goods) % 10 == 0:
        max_index -= 1
    if 0 <= current_index <= max_index:
        if data == 'user':
            back_data = 'profile'
            pre_back = 'bought_items'
        else:
            back_data = f'check-user_{data}'
            pre_back = f'user-items_{data}'
        markup = user_items_list(bought_goods, data, back_data, pre_back, current_index, max_index)
        await bot.edit_message_text(message_id=call.message.message_id,
                                    chat_id=call.message.chat.id,
                                    text='Your items:',
                                    reply_markup=markup)
    else:
        await bot.answer_callback_query(callback_query_id=call.id, text="❌ Page not found")


async def bought_item_info_callback_handler(call: CallbackQuery):
    item_id = call.data.split(":")[1]
    back_data = call.data.split(":")[2]
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    item = get_bought_item_info(item_id)
    await bot.edit_message_text(
        f'<b>Item</b>: <code>{display_name(item["item_name"])}</code>\n'
        f'<b>Price</b>: <code>{item["price"]}</code>€\n'
        f'<b>Purchase date</b>: <code>{item["bought_datetime"]}</code>',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=back(back_data))


async def rules_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    rules_data = TgConfig.RULES

    if rules_data:
        await bot.edit_message_text(rules_data, chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=rules())
        return

    await call.answer(text='❌ Rules were not added')


async def help_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    user_lang = get_user_language(user_id) or 'en'
    help_text = t(user_lang, 'help_info', helper=TgConfig.HELPER_URL)
    await bot.edit_message_text(
        help_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=back('profile')
    )


async def profile_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    user = call.from_user
    TgConfig.STATE[user_id] = None
    user_info = check_user(user_id)
    user_lang = user_info.language or 'en'
    balance = user_info.balance
    operations = select_user_operations(user_id)
    overall_balance = 0

    if operations:

        for i in operations:
            overall_balance += i

    items = select_user_items(user_id)
    markup = profile(items, user_lang)
    await bot.edit_message_text(text=f"👤 <b>Profile</b> — {user.first_name}\n🆔"
                                     f" <b>ID</b> — <code>{user_id}</code>\n"
                                     f"💳 <b>Balance</b> — <code>{balance}</code> €\n"
                                     f"💵 <b>Total topped up</b> — <code>{overall_balance}</code> €\n"
                                     f" 🎁 <b>Items purchased</b> — {items} pcs",
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=markup,
                                parse_mode='HTML')


async def replenish_balance_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    message_id = call.message.message_id

    # proceed if NowPayments API key is configured
    if EnvKeys.NOWPAYMENTS_API_KEY:
        TgConfig.STATE[f'{user_id}_message_id'] = message_id
        TgConfig.STATE[user_id] = 'process_replenish_balance'
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=message_id,
            text='💰 Enter the top-up amount:',
            reply_markup=back('back_to_menu')
        )
        return

    # fallback if API key missing
    await call.answer('❌ Top-up is not configured.')



async def process_replenish_balance(message: Message):
    bot, user_id = await get_bot_user_ids(message)

    text = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = None
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if not text.isdigit() or int(text) < 5 or int(text) > 10000:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text="❌ Invalid top-up amount. "
                                         "The amount must be between 5€ and 10 000€",
                                    reply_markup=back('replenish_balance'))
        return

    TgConfig.STATE[f'{user_id}_amount'] = text
    markup = crypto_choice()
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text=f'💵 Top-up amount: {text}€. Choose payment method:',
                                reply_markup=markup)


async def pay_yoomoney(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    amount = TgConfig.STATE.pop(f'{user_id}_amount', None)
    if not amount:
        await call.answer(text='❌ Invoice not found')
        return

    fake = type('Fake', (), {'text': amount, 'from_user': call.from_user})
    label, url = quick_pay(fake)
    sleep_time = int(TgConfig.PAYMENT_TIME)
    lang = get_user_language(user_id) or 'en'
    markup = payment_menu(url, label, lang)
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=f'💵 Top-up amount: {amount}€.\n'
                                     f'⌛️ You have {int(sleep_time / 60)} minutes to pay.\n'
                                     f'<b>❗️ After payment press "Check payment"</b>',
                                reply_markup=markup)
    start_operation(user_id, amount, label, call.message.message_id)
    _remember_invoice_context(user_id, label)
    await asyncio.sleep(sleep_time)
    info = get_unfinished_operation(label)
    if info:
        _, _, _ = info
        status = await check_payment_status(label)
        if status not in ('paid', 'success'):
            finish_operation(label)
            context = TgConfig.STATE.pop(f'invoice_ctx_{label}', None)
            await _notify_invoice_cancelled(bot, user_id, lang, context)


async def crypto_payment(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    currency = call.data.split('_')[1]
    amount = TgConfig.STATE.pop(f'{user_id}_amount', None)
    if not amount:
        await call.answer(text='❌ Invoice not found')
        return

    payment_id, address, pay_amount = create_payment(float(amount), currency)

    sleep_time = int(TgConfig.PAYMENT_TIME)
    lang = get_user_language(user_id) or 'en'
    expires_at = (
        datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)
    ).strftime('%H:%M')
    markup = crypto_invoice_menu(payment_id, lang)
    text = t(
        lang,
        'invoice_message',
        amount=pay_amount,
        currency=currency,
        address=address,
        expires_at=expires_at,
    )

    # Generate QR code for the address
    qr = qrcode.make(address)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)

    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    sent = await bot.send_photo(
        chat_id=call.message.chat.id,
        photo=buf,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup,
    )
    start_operation(user_id, amount, payment_id, sent.message_id)
    _remember_invoice_context(user_id, payment_id)
    await asyncio.sleep(sleep_time)
    info = get_unfinished_operation(payment_id)
    if info:
        _, _, _ = info
        status = await check_payment(payment_id)
        if status not in ('finished', 'confirmed', 'sending'):
            finish_operation(payment_id)
            context = TgConfig.STATE.pop(f'invoice_ctx_{payment_id}', None)
            await _notify_invoice_cancelled(bot, user_id, lang, context)


async def checking_payment(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    message_id = call.message.message_id
    label = call.data[6:]
    info = get_unfinished_operation(label)
    lang = get_user_language(user_id) or 'en'

    if info:
        user_id_db, operation_value, _ = info
        payment_status = await check_payment_status(label)
        if payment_status is None:
            payment_status = await check_payment(label)

        if payment_status in ("success", "paid", "finished", "confirmed", "sending"):
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            referral_id = get_user_referral(user_id)
            finish_operation(label)

            if referral_id and TgConfig.REFERRAL_PERCENT != 0:
                referral_percent = TgConfig.REFERRAL_PERCENT
                referral_operation = round((referral_percent/100) * operation_value)
                update_balance(referral_id, referral_operation)
                await bot.send_message(referral_id,
                                       f'✅ You received {referral_operation}€ '
                                       f'from your referral {call.from_user.first_name}',
                                       reply_markup=close())

            create_operation(user_id, operation_value, formatted_time)
            update_balance(user_id, operation_value)
            context = TgConfig.STATE.pop(f'invoice_ctx_{label}', None)
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=message_id,
                                        text=f'✅ Balance topped up by {operation_value}€',
                                        reply_markup=back('profile'))
            username = f'@{call.from_user.username}' if call.from_user.username else call.from_user.full_name
            await bot.send_message(
                EnvKeys.OWNER_ID,
                f'User {username} topped up {operation_value}€'
            )
            if context:
                item_name = context.get('item')
                price = context.get('price')
                if item_name and price is not None:
                    text = t(
                        lang,
                        'confirm_purchase',
                        item=display_name(item_name),
                        price=format_amount(price),
                    )
                    await bot.send_message(
                        user_id,
                        text,
                        reply_markup=confirm_purchase_menu(item_name, lang),
                    )
                    TgConfig.STATE.pop(f'{user_id}_amount', None)
        else:
            await call.answer(text='❌ Payment was not successful')
    else:
        await call.answer(text='❌ Invoice not found')


async def _cancel_invoice_and_cleanup(
    call: CallbackQuery,
    bot,
    user_id: int,
    invoice_id: str,
    lang: str,
    info: tuple[int, int, int | None] | None = None,
) -> None:
    """Delete invoice artifacts and release any reserved state."""

    record = info if info is not None else get_unfinished_operation(invoice_id)
    if record:
        _, _, msg_id = record
        finish_operation(invoice_id)
        if msg_id:
            with suppress(MessageCantBeDeleted, MessageToDeleteNotFound, Exception):
                await bot.delete_message(call.message.chat.id, msg_id)

    context = TgConfig.STATE.pop(f'invoice_ctx_{invoice_id}', None)
    for key in (
        f'{user_id}_invoice_for_purchase',
        f'{user_id}_amount',
        f'{user_id}_pending_item',
        f'{user_id}_price',
    ):
        TgConfig.STATE.pop(key, None)

    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound, Exception):
        await bot.delete_message(call.message.chat.id, call.message.message_id)

    await _notify_invoice_cancelled(bot, user_id, lang, context)


async def cancel_payment(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    invoice_id = call.data.split('_', 1)[1]
    lang = get_user_language(user_id) or 'en'
    if get_unfinished_operation(invoice_id):
        prompt = 'Are you sure you want to cancel payment?'
        kwargs = dict(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=confirm_cancel(invoice_id, lang),
        )
        if call.message.text:
            await bot.edit_message_text(prompt, **kwargs)
        else:
            await bot.edit_message_caption(caption=prompt, **kwargs)
    else:
        await call.answer()
        await _cancel_invoice_and_cleanup(call, bot, user_id, invoice_id, lang)



async def confirm_cancel_payment(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    invoice_id = call.data.split('_', 2)[2]
    lang = get_user_language(user_id) or 'en'

    info = get_unfinished_operation(invoice_id)
    await _cancel_invoice_and_cleanup(call, bot, user_id, invoice_id, lang, info)
    await call.answer()

async def change_language(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    current_lang = get_user_language(user_id) or 'en'
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('English \U0001F1EC\U0001F1E7', callback_data='set_lang_en'),
        InlineKeyboardButton('Русский \U0001F1F7\U0001F1FA', callback_data='set_lang_ru'),
        InlineKeyboardButton('Lietuvi\u0173 \U0001F1F1\U0001F1F9', callback_data='set_lang_lt')
    )
    await bot.edit_message_text(
        t(current_lang, 'choose_language'),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )




async def set_language(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    try:
        # 1) Persist language choice
        lang_code = call.data.split('_')[-1]
        update_user_language(user_id, lang_code)

        # Ensure DB user exists (some flows reached here before /start created it)
        user = check_user(user_id)
        if not user:
            # Create a minimal user row with role=1 (user)
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            create_user(telegram_id=user_id, registration_date=current_time, referral_id=None, role=1,
                        username=call.from_user.username)
            user = check_user(user_id)

        # 2) Clean up the inline prompt (best-effort)
        with suppress(Exception):
            await call.message.delete()

        # 3) Build menu
        try:
            role = check_role(user_id)
        except Exception:
            # Fallback to role 1 if role lookup fails for any reason
            role = 1

        balance = (user.balance if user else 0)
        purchases = select_user_items(user_id)
        markup = main_menu(role, TgConfig.CHANNEL_URL, TgConfig.PRICE_LIST_URL, lang_code)
        text = build_menu_text(call.from_user, balance, purchases, lang_code)

        # 4) Try media first (best-effort; never block the menu)
        with suppress(Exception):
            await send_start_media(bot, user_id)

        # 5) Always send the menu
        await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)

    except Exception as e:
        # If anything goes wrong, still try to send a minimal menu in English
        with suppress(Exception):
            fallback_markup = main_menu(1, TgConfig.CHANNEL_URL, TgConfig.PRICE_LIST_URL, 'en')
            await bot.send_message(chat_id=user_id, text="✅ Language set. Here's the menu:", reply_markup=fallback_markup)
        raise



def register_user_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(shop_callback_handler,
                                       lambda c: c.data == 'shop')
    dp.register_callback_query_handler(dummy_button,
                                       lambda c: c.data == 'dummy_button')
    dp.register_callback_query_handler(profile_callback_handler,
                                       lambda c: c.data == 'profile')
    dp.register_callback_query_handler(rules_callback_handler,
                                       lambda c: c.data == 'rules')
    dp.register_callback_query_handler(help_callback_handler,
                                       lambda c: c.data == 'help')
    dp.register_callback_query_handler(replenish_balance_callback_handler,
                                       lambda c: c.data == 'replenish_balance')
    dp.register_callback_query_handler(price_list_callback_handler,
                                       lambda c: c.data == 'price_list')
    dp.register_callback_query_handler(bought_items_callback_handler,
                                       lambda c: c.data == 'bought_items', state='*')
    dp.register_callback_query_handler(back_to_menu_callback_handler,
                                       lambda c: c.data == 'back_to_menu',
                                       state='*')
    dp.register_callback_query_handler(close_callback_handler,
                                       lambda c: c.data == 'close', state='*')
    dp.register_callback_query_handler(change_language,
                                       lambda c: c.data == 'change_language', state='*')
    dp.register_callback_query_handler(set_language,
                                       lambda c: c.data.startswith('set_lang_'), state='*')

    dp.register_callback_query_handler(navigate_bought_items,
                                       lambda c: c.data.startswith('bought-goods-page_'), state='*')
    dp.register_callback_query_handler(bought_item_info_callback_handler,
                                       lambda c: c.data.startswith('bought-item:'), state='*')
    dp.register_callback_query_handler(items_list_callback_handler,
                                       lambda c: c.data.startswith('category_'), state='*')
    dp.register_callback_query_handler(item_info_callback_handler,
                                       lambda c: c.data.startswith('item_'), state='*')
    dp.register_callback_query_handler(confirm_buy_callback_handler,
                                       lambda c: c.data.startswith('confirm_'), state='*')
    dp.register_callback_query_handler(apply_promo_callback_handler,
                                       lambda c: c.data.startswith('applypromo_'), state='*')
    dp.register_callback_query_handler(buy_item_callback_handler,
                                       lambda c: c.data.startswith('buy_'), state='*')
    # Invoices disabled
    # dp.register_callback_query_handler(create_purchase_invoice,
    #                                    lambda c: c.data.startswith('purchase_invoice_'), state='*')
    dp.register_callback_query_handler(back_to_shortfall,
                                       lambda c: c.data.startswith('back_shortfall_'), state='*')
    dp.register_callback_query_handler(pay_yoomoney,
                                       lambda c: c.data == 'pay_yoomoney', state='*')
    dp.register_callback_query_handler(crypto_payment,
                                       lambda c: c.data.startswith('crypto_'), state='*')
    dp.register_callback_query_handler(cancel_payment,
                                       lambda c: c.data.startswith('cancel_'), state='*')
    dp.register_callback_query_handler(confirm_cancel_payment,
                                       lambda c: c.data.startswith('confirm_cancel_'), state='*')
    dp.register_callback_query_handler(checking_payment,
                                       lambda c: c.data.startswith('check_'), state='*')
    dp.register_callback_query_handler(process_home_menu,
                                       lambda c: c.data == 'home_menu', state='*')

    dp.register_message_handler(process_replenish_balance,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'process_replenish_balance')
    dp.register_message_handler(process_promo_code,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'wait_promo')
    dp.register_message_handler(pavogti,
                                commands=['pavogti'])
    dp.register_callback_query_handler(pavogti_item_callback,
                                       lambda c: c.data.startswith('pavogti_item_'))
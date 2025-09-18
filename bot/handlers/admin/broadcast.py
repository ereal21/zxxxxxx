import asyncio
from contextlib import suppress

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram.utils.exceptions import BotBlocked, MessageCantBeDeleted, MessageToDeleteNotFound

from bot.keyboards import back, close
from bot.database.methods import check_role, get_all_users
from bot.database.models import Permission
from bot.misc import TgConfig
from bot.logger_mesh import logger
from bot.handlers.other import get_bot_user_ids


async def send_message_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'waiting_for_message'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role & Permission.BROADCAST:
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text='Send the message for broadcast:',
                                    reply_markup=back("console"))
        return
    await call.answer('Insufficient rights')


async def broadcast_messages(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    user_info = await bot.get_chat(user_id)
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    source_chat_id = message.chat.id
    source_message_id = message.message_id
    TgConfig.STATE[user_id] = None
    reply_markup = close()
    users = get_all_users()
    max_users = 0
    for user_row in users:
        max_users += 1
        user_id = user_row[0]
        await asyncio.sleep(0.1)
        try:
            await bot.copy_message(chat_id=int(user_id),
                                   from_chat_id=source_chat_id,
                                   message_id=source_message_id,
                                   reply_markup=reply_markup)
        except BotBlocked:
            pass
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send broadcast to %s: %s", user_id, exc)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Broadcast finished',
                                reply_markup=back("console"))
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await bot.delete_message(chat_id=source_chat_id,
                                 message_id=source_message_id)
    TgConfig.STATE.pop(f'{user_id}_message_id', None)
    logger.info(f"User {user_info.id} ({user_info.first_name})"
                f" performed a broadcast. Message was sent to {max_users} users.")


def register_mailing(dp: Dispatcher) -> None:
    dp.register_callback_query_handler(send_message_callback_handler,
                                       lambda c: c.data == 'send_message')

    dp.register_message_handler(
        broadcast_messages,
        lambda c: TgConfig.STATE.get(c.from_user.id) == 'waiting_for_message',
        content_types=ContentType.ANY,
    )


import re, time, asyncio
from collections import deque, defaultdict
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Deque

DEFAULT_RATE_LIMIT = 12  # messages
DEFAULT_TIME_WINDOW = 15  # seconds
MIN_MESSAGE_INTERVAL = 0.7  # per user (seconds)

SUSPICIOUS_PATTERNS = [
    r"(free\s*crypto|giveaway|airdrop|claim\s*prize)",
    r"(cheap\s*(followers|views)|boost\s*your)",
    r"(http[s]?://\S*?t\.me/joinchat)",
    r"(http[s]?://\S*?bit\.ly|tinyurl\.com|goo\.gl)",
]

URL_RE = re.compile(r"http[s]?://\S+", re.IGNORECASE)
BAD_RE = re.compile("|".join(SUSPICIOUS_PATTERNS), re.IGNORECASE)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_TIME_WINDOW):
        super().__init__()
        self.limit = limit
        self.window = window
        self.msg_times: Dict[int, Deque[float]] = defaultdict(deque)
        self.last_time: Dict[int, float] = {}

    async def on_process_message(self, message: Message, data: dict):
        uid = message.from_user.id if message.from_user else 0
        now = time.monotonic()
        dq = self.msg_times[uid]
        dq.append(now)
        while dq and now - dq[0] > self.window:
            dq.popleft()
        last = self.last_time.get(uid, 0.0)
        self.last_time[uid] = now
        too_fast = (now - last) < MIN_MESSAGE_INTERVAL
        too_many = len(dq) > self.limit
        if too_fast or too_many:
            try:
                await message.answer("🚦 Slow down a bit to avoid spam limits.")
            except Exception:
                pass
            raise asyncio.CancelledError()

class SpamFilterMiddleware(BaseMiddleware):
    def __init__(self, max_urls: int = 3, max_length: int = 3000):
        super().__init__()
        self.max_urls = max_urls
        self.max_length = max_length

    async def on_process_message(self, message: Message, data: dict):
        if not message.text:
            return
        text = message.text or ""
        if len(text) > self.max_length:
            await message.reply("✋ Message too long. Please shorten it.")
            raise asyncio.CancelledError()

        urls = URL_RE.findall(text)
        if len(urls) > self.max_urls or BAD_RE.search(text):
            await message.reply("⚠️ Your message looks suspicious (too many links or flagged keywords).")
            raise asyncio.CancelledError()

from bot.utils.consent import is_opted_in
from bot.misc.config import TgConfig

class ConsentGateMiddleware(BaseMiddleware):
    async def on_process_message(self, message: Message, data: dict):
        if message.chat and message.chat.type != 'private':
            return
        if not message.from_user:
            return
        uid = message.from_user.id
        has_pending = TgConfig.STATE.get(f"captcha_expected_{uid}") is not None
        if is_opted_in(uid) or has_pending:
            return
        if message.text and message.text.startswith("/start"):
            return
        try:
            await message.answer("🔒 Please /start and complete the CAPTCHA to use the bot.")
        finally:
            raise asyncio.CancelledError()

from abc import ABC
from typing import Final


class TgConfig(ABC):
    STATE: Final = {}
    BASKETS: Final = {}
    CHANNEL_URL: Final = 'https://t.me/kepykla'
    HELPER_URL: Final = '@Karunele'
    PRICE_LIST_URL: Final = 'https://t.me/+iXbi98gT0v5lOTNk'
    GROUP_ID: Final = -988765433
    REFERRAL_PERCENT = 5
    PAYMENT_TIME: Final = 1800
    RULES: Final = 'insert your rules here'
    START_PHOTO_PATH: Final = r'C:\Users\Administrator\Downloads\photo_2025-08-17_23-09-19.jpg'
    START_VIDEO_PATH: Final = r'C:\Users\Administrator\Desktop\bot\1.mp4'

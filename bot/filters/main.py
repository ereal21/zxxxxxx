from aiogram import Dispatcher


from .middlewares import RateLimitMiddleware, SpamFilterMiddleware, ConsentGateMiddleware

def register_all_filters(dp: Dispatcher):
    dp.middleware.setup(RateLimitMiddleware())
    dp.middleware.setup(SpamFilterMiddleware())
    dp.middleware.setup(ConsentGateMiddleware())


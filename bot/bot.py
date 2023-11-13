import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

if __name__ == '__main__':
    from handlers.handlers import dp
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)

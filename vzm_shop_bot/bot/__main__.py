import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from .config import load_config, Config
from .handlers import router
from .db import init_db

async def main():
    config = load_config()
    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp.include_router(router)
    dp["config"] = config

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, config=config)

if __name__ == "__main__":
    asyncio.run(main())

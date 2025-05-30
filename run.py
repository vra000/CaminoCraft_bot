import asyncio, logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router
from app.server_status import init_status, look_previous_status
from app.database.models import async_main
from app.database.timers import timer_watcher


async def main():
    await async_main()
    await init_status()
    asyncio.create_task(look_previous_status())
    asyncio.create_task(timer_watcher())
    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
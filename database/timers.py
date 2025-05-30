import asyncio
from app.database.requests import get_all_users_timers, delete_process_reports

active_timers = set()

async def timer_watcher(interval=60):
    while True:
        users = await get_all_users_timers()
        for user in  users:
            if user.user_id not in active_timers:
                asyncio.create_task(watch_and_remove(user.user_id))
        await asyncio.sleep(interval)

async def watch_and_remove(user_id):
    await delete_process_reports(user_id)
    active_timers.discard(user_id)
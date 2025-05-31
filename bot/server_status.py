import asyncio
from mcstatus import JavaServer
from app.bot.config import HOST

online = '🟢 Онлайн'
offline = '🔴 Оффлайн'

current_status = None
previous_status = None

async def is_server_online():
    global current_status
    try:
        server = JavaServer.lookup(HOST)
        status = await asyncio.to_thread(server.status)
        current_status = online
        return online
    except Exception:
        current_status = offline
        print("Сервер оффлайн или не доступен")
        return offline

async def look_previous_status():
    global previous_status, current_status
    while True:
        new_status = await is_server_online()
        if new_status != current_status:
            previous_status = current_status
            current_status = new_status
            print(f"Новый статус: {current_status}")
        await asyncio.sleep(15)

async def status_changed():
    return current_status != previous_status

async def init_status():
    global current_status, previous_status
    current_status = await is_server_online()
    previous_status = current_status

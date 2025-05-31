import asyncio

from app.bot.database.models import async_session
from app.bot.database.models import User
from sqlalchemy import select
from sqlalchemy import func
from typing import Optional


async def set_user_data(user_id: int, username: Optional[str]=None, description:Optional[str]=None, photo_id:Optional[str]=None, process:int=0):
    #Ищем пользователя
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        if not user:
            user = User(user_id=user_id, username=username, description=description, photo_id=photo_id, process=process)
            session.add(user)
        else:
            if username is not None:
                user.username = username
            if description is not None:
                user.description = description
            if photo_id is not None:
                user.photo_id = photo_id
            user.process = process
        await session.commit()

async def reset_user_data(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id==user_id))
        if user:
            await session.delete(user)
            await session.commit()

async def get_reports():
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.process == 1, User.punished == False)
        )
    reports = result.scalars().all()
    return reports

async def get_report_by_user(user_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.user_id == user_id, User.process == 1, User.punished == False))

async def reports_count():
    async with async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(User.process == 1, User.punished == False)
        )
        reports_amount = result.scalar_one()
        return reports_amount
    
async def accept_report(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id, User.process == 1, User.punished == False))
        if user:
            user.process = 2
            await session.commit()
            return True
        return False
    
async def cancel_report(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id, User.process == 1, User.punished == False))
        if user:
            user.process = 3
            await session.commit()
            return True
        return False
    
async def punish_report(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id, User.process == 1, User.punished == False))
        if user:
            user.punished = True
            await session.commit()
            return True
        return False

async def is_punished(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        return bool(user.punished) if user else False

async def delete_process_reports(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        if not user:
            return
        if user.process == 0:
            await asyncio.sleep(86400) # 1 день

        elif user.process == 1:
            await asyncio.sleep(604800) # Неделя

        elif user.process == 2:
            await asyncio.sleep(1209600) # Две недели

        elif user.process == 3:
            await asyncio.sleep(172800) # 2 дня
        
        elif user.punished:
            await asyncio.sleep(10800) # 3 часа

        user = await session.scalar(select(User).where(User.user_id == user_id))
        if user:
            await session.delete(user)
            await session.commit()

async def get_all_users_timers():
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                (User.process.in_([0, 1, 2, 3])) | (User.punished == True)
            )
        )
        return result.scalars().all()

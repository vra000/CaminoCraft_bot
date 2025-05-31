import asyncio
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import HOST, ADMIN_ID
import app.bot.database.requests as rq
import app.bot.keyboards as kb
from app.bot.server_status import online, offline, is_server_online
import app.bot.bug_reports as br


router = Router()

async def delete_message_later(message, delay=None):
    if delay is None:
        try:
            await message.delete()
        except Exception:
            pass
    elif delay and delay > 0:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception:
            pass

async def reports_list(call: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    try:
        await call.message.edit_text(
            text,
            reply_markup=await kb.admin_reports(),
            parse_mode=parse_mode
        )
    except Exception:
        await call.message.delete()
        await call.bot.send_message(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )


@router.message(Command('start'))
async def cmd_anwser(message: Message, state: FSMContext):
    data = await state.get_data()
    old_msg_id = data.get('menu_msg_id')
    if old_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
        except Exception:
            pass
    msg = await message.answer('Добро пожаловат в информационную панель.', reply_markup=kb.main_keyboard)
    await state.update_data(menu_msg_id=msg.message_id)

@router.callback_query(F.data.in_({'mInfo', 'mStatus', 'update', 'mBug_report', 'back'}))
async def main_callback_query(call: CallbackQuery):
    if call.data == 'mInfo':
        await call.answer()
        await call.message.edit_text(
            'ℹ *Информация*\n\nВ данном разделе есть вся информация о контактах.',
            parse_mode='Markdown',
            reply_markup=kb.info_keyboard
        )

    if call.data == 'mStatus':
        print("Статус")
        status = await is_server_online()
        if status == online:
            await call.message.edit_text(
                f'🌐 *Статус сервера*\n\nСервер: {HOST}\nСтатус: {online}',
                parse_mode='Markdown',
                reply_markup=kb.status_keyboard
            )
        elif status == offline:
            await call.message.edit_text(
                f'Сервер: {HOST}\nСтатус: {offline}',
                reply_markup=kb.status_keyboard
            )
        else:
            await call.answer(text="Статус сервера ещё не определён. Попробуйте чуть позже.", show_alert=False)

    elif call.data == 'update':
        from app.bot.server_status import previous_status
        prev = previous_status
        status = await is_server_online()
        if status != prev:
            import app.bot.server_status
            app.bot.server_status.previous_status = status

            if status == online:
                await call.message.edit_text(
                    f'Сервер: {HOST}\nСтатус: {online}\nИгроки:',
                    reply_markup=kb.status_keyboard
                )
            elif status == offline:
                await call.message.edit_text(
                    f'Сервер: {HOST}\nСтатус: {offline}',
                    reply_markup=kb.status_keyboard
                )
        else:
            await call.answer(text="Статус сервера не изменился", show_alert=True)

    if call.data == 'mBug_report':
        await call.message.edit_text(
            '🐞 *Репорт бага*\n\nЕсли вы нашли баг в системе (что-то работает не так), то подробно описав проблему, вы можете оставить заявку здесь.',
            parse_mode='Markdown',
            reply_markup=kb.report_keyboard
        )

    elif call.data == 'back':
        await call.message.edit_text(
            'Добро пожаловать в информационную панель.',
            reply_markup=kb.main_keyboard
        )

@router.callback_query(F.data == 'report_asking')
async def ask_desk(call: CallbackQuery, state: FSMContext):
    if await rq.is_punished(call.from_user.id):
        await call.answer('Вы были временно наказаны за неккоректный репорт ⚠')
    else:
        await rq.set_user_data(user_id=call.from_user.id,username=call.from_user.username)
        await state.set_state(br.BugReport.desc)
        await call.message.edit_text(
            '*Описание проблемы*\n\nПожалуйста, как можно более подробно опишите проблему, с которой вы столкнулись. В противном случае репорт может быть отклонён.\n\n*Формат:* 10-500 символов.',
            parse_mode="Markdown",
            reply_markup=kb.report_desc
        )

@router.message(br.BugReport.desc, F.text)
async def save_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)

@router.callback_query(F.data == 'confirm_desc')
async def ask_photo(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    description = data.get('desc', '')
    char_count = len(description)
    if char_count <10 or char_count >500:
        sent = 'Описание слишком короткое или слишком длинное ❌'
        await call.bot.send_message(
            chat_id=call.message.chat.id,
            text=sent
        )
        asyncio.create_task(delete_message_later(sent, delay=5))
    else:
        await rq.set_user_data(user_id=call.from_user.id,description=description)
        sent = await call.bot.send_message(chat_id=call.message.chat.id, text='Описание добавлено ➕')
        await state.set_state(br.BugReport.photo)
        await call.message.edit_text(
        '*Отправка фото*\n\nДля быстрого решения проблемы мы *настоятельно* рекомендуем отправить фото, относящееся к ошибке.\n\n*Формат:* Фото ошибки *без надписей к фото*',
            parse_mode='Markdown',
            reply_markup=kb.report_screenshot
        )
        asyncio.create_task(delete_message_later(sent, delay=10))

@router.message(br.BugReport.photo, F.photo)
async def save_photo(message: Message, state: FSMContext):
    if message.caption:
        await message.answer('Отправьте фото без текста внутри него ❌')
    else:
        photo_id = message.photo[-1].file_id
        await rq.set_user_data(user_id=message.from_user.id, photo_id=photo_id)
        await state.update_data(photo=photo_id)
        sent = await message.answer('Фото добавлено ➕')
        asyncio.create_task(delete_message_later(sent, delay=10))

@router.message(br.BugReport.photo)
async def check_photo(message: Message, state: FSMContext):
    sent = 'Вы можете отправить только фото!'
    await message.answer(sent)
    asyncio.create_task(delete_message_later(sent, delay=5))

@router.callback_query(F.data == 'confirm_screenshot')
async def confirm_photo(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo = data.get('photo', '')
    if not photo:
        sent = 'Вы не прикрепили фото!'
        await call.bot.send_message(chat_id=call.message.chat.id,text=sent)
        asyncio.create_task(delete_message_later(sent, delay=5))
    else:
        await state.set_state(br.BugReport.confirm)
        await call.message.edit_text(
            '*Заполнение формы завершено.*\n\nВы можете отправить репорт на рассмотрение или же полностью его отменить.',
            parse_mode='Markdown',
            reply_markup=kb.report_confirm
        )

@router.callback_query(F.data == 'skip_screenshot')
async def skip_photo(call: CallbackQuery, state: FSMContext):
    await rq.set_user_data(user_id=call.from_user.id,photo_id=None)
    await state.update_data(photo=None)
    await call.message.edit_text(
        '*Заполнение формы завершено.*\n\n*СКРИНШОТ НЕ ПРИКРЕПЛЁН*\nВы можете отправить репорт на рассмотрение или же полностью его отменить.',
        parse_mode='Markdown',
        reply_markup=kb.report_confirm
    )

@router.callback_query(F.data == 'report_confirm')
async def send_report(call: CallbackQuery, state: FSMContext):
    await state.set_state(br.BugReport.confirm)
    data = await state.get_data()
    await rq.set_user_data(user_id=call.from_user.id, process=1)
    await call.message.edit_text(
        'Добро пожаловать в информационную панель.',
        reply_markup=kb.main_keyboard)
    await asyncio.sleep(1)
    await call.bot.send_message(chat_id=call.message.chat.id, text=f'Вы отправили баг-репорт ✅\nОписание:{data.get("desc")}\nФото:{data.get("photo")}')
    await state.clear()

@router.callback_query(F.data == 'report_cancel')
async def cancel_report(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await rq.reset_user_data(user_id=call.from_user.id)
    await call.message.edit_text(
        'Если вы нашли баг в системе (что-то работает не так), то подробно описав проблему, вы можете оставить заявку здесь.',
        reply_markup=kb.report_keyboard 
    )
    sent = 'Вы отменили репорт ❌'
    delete_message_later(sent, delay=10)


@router.message(Command('admin'))
async def main_admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await message.answer('Админ-панель', reply_markup=kb.admin_keyboard)

@router.callback_query(F.data == 'reports_list')
async def reports_panel(call: CallbackQuery):
    count = await rq.reports_count()
    await reports_list(
        call,
        text=f'Доступно: {count} репортов',
        reply_markup=await kb.admin_reports()
    )

@router.callback_query(F.data == 'reports_back')
async def back_reprots(call: CallbackQuery):
    await call.message.edit_text('Админ-панель', reply_markup=kb.admin_keyboard)

@router.callback_query(F.data.startswith('reports_'))
async def report_detail(call: CallbackQuery):
    user_id = call.data.split('_', 1)[1]
    report = await rq.get_report_by_user(user_id)
    if not report:
        await call.answer('Репорт не найден', show_alert=True)
        return

    username = report.username or 'Неизвестно'
    description = report.description
    photo_id = report.photo_id or 'Нет фото'

    try:
        await call.message.delete()
    except Exception:
        pass
    text = (
        f'Репорт от пользователя *{username}*\n\n'
        f'*Описание:* {description}'
        )
    if photo_id:
        await call.bot.send_photo(
            chat_id=call.message.chat.id,
            photo=photo_id,
            caption=text,
            reply_markup=await kb.report_look(user_id),
            parse_mode='Markdown'
        )
    else:
        await call.bot.send_message(
            chat_id=call.message.chat.id,
            text=text + '\n*Фото:* Без фото',
            reply_markup=await kb.report_look(user_id),
            parse_mode='Markdown'
        )

@router.callback_query(F.data.startswith('report_accept_'))
async def report_accept(call: CallbackQuery):
    user_id = call.data.split('_', 2)[2]
    await rq.accept_report(user_id)
    await call.message.delete()
    count = await rq.reports_count()
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text=f'Доступно: {count} репортов',
        reply_markup=await kb.admin_reports()
    )
    sent = await call.bot.send_message(chat_id=call.message.chat.id, text='Репорт решён ✅')
    asyncio.create_task(delete_message_later(sent, delay=10))

@router.callback_query(F.data.startswith('report_cancel_'))
async def report_cancel(call: CallbackQuery):
    user_id = call.data.split('_', 2)[2]
    await rq.cancel_report(user_id)
    count = await rq.reports_count()
    await reports_list(
        call,
        text=f'Доступно: {count} репортов',
        reply_markup=await kb.admin_reports()
    )
    sent = await call.bot.send_message(chat_id=call.message.chat.id, text='Репорт отклонён ❌')
    asyncio.create_task(delete_message_later(sent, delay=10))

@router.callback_query(F.data.startswith('report_punish_'))
async def report_punish(call: CallbackQuery):
    user_id = call.data.split('_', 2)[2]
    await rq.punish_report(user_id)
    count = await rq.reports_count()
    await reports_list(
        call,
        text=f'Доступно: {count} репортов',
        reply_markup=await kb.admin_reports()
    )
    sent = await call.bot.send_message(chat_id=call.message.chat.id, text='Пользователь наказан 🔔')
    asyncio.create_task(delete_message_later(sent, delay=10))

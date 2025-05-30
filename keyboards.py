from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import app.database.requests as rq

# Основная панель
main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='ℹ Информация', callback_data='mInfo'),
        InlineKeyboardButton(text='🌐 Статус сервера', callback_data='mStatus')
    ],
    [
        InlineKeyboardButton(text='🐞 Репорт бага', callback_data='mBug_report')
    ]
])

# Инфо-панель

info_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='VK', url='https://vk.com/caminocraft'),
        InlineKeyboardButton(text='Telegram', url='https://t.me/caminocraft'),
    ],
    # Второй ряд
    [
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back')
    ]
])

# Статус-панель

status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back'),
        InlineKeyboardButton(text='🔄 Обновить', callback_data='update')
    ]
])

# Репорты

# Основная панель репортов
report_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back'),
        InlineKeyboardButton(text='Перейти к заполнению', callback_data='report_asking')
    ]
])

## Описание
report_desc = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='⬅️ Меню репортов', callback_data='report_cancel'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_desc')
    ]
])

## Фото
report_screenshot = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='⬅️ Меню репортов', callback_data='report_cancel'),
        InlineKeyboardButton(text='➡ Пропустить', callback_data='skip_screenshot')
    ],
    [
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_screenshot')
    ]
])

## Подтверждение
report_confirm = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='❌ Отменить', callback_data='report_cancel'),
        InlineKeyboardButton(text='✉ Отправить', callback_data='report_confirm')
    ]
])

# Админ-панель

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='🔍 Репорты', callback_data='reports_list')
    ]
])

async def admin_reports():
    reports = await rq.get_reports()
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='reports_back'))
    for report in reports:
        text=f'№ {report.number}'
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f'reports_{report.user_id}'))
    return keyboard.as_markup()

async def report_look(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Решено', callback_data=f'report_accept_{user_id}'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'report_cancel_{user_id}'),
            InlineKeyboardButton(text='⚠ Наказать', callback_data=f'report_punish_{user_id}')
        ],
        [
            InlineKeyboardButton(text='⬅️ Назад', callback_data='reports_list')
        ]
    ])
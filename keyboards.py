from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поддержка")],
        [KeyboardButton(text="Словарь")],
        [KeyboardButton(text="Новости")],
        [KeyboardButton(text="Собеседник")],
    ],
    resize_keyboard=True
)

continue_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продолжить поиск", callback_data="continue")],
    [InlineKeyboardButton(text="В меню", callback_data="menu")]
])

support_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="В меню", callback_data="menu")],
    [InlineKeyboardButton(text="Написать разработчику", url="")],
    [InlineKeyboardButton(text="Правила и политика", callback_data="rules")]
])

companion_role_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сокомандник (teen style)", callback_data="role_teammate")],
    [InlineKeyboardButton(text="Тренер (motivator style)", callback_data="role_coach")]
])

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

# После ответа в Словаре/Новостях
continue_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить поиск", callback_data="continue")],
        [InlineKeyboardButton(text="В меню", callback_data="menu")]
    ]
)

# Поддержка
support_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="В меню", callback_data="menu")]
    ]
)
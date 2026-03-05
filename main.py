import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from DB import init_db, get_user_state, set_user_mode, reset_all_modes, set_dictionary_direction
from SOBESEDNIK import get_companion_response
from Neuro import get_dictionary_response   # ← новый
from news import get_football_news              # ← твой парсер + Qwen

from keyboards import main_menu, continue_kb, support_kb

BOT_TOKEN = '8508213773:AAGbNfPkTCi4OMlPxhm_vwlbYyw7G9yNpMU'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет, mate! Я твой британский футбольный бот для практики английского.\n"
        "Выбирай режим кнопками ниже 👇",
        reply_markup=main_menu
    )

# ==================== ПОДДЕРЖКА ====================
@dp.message(F.text == "Поддержка")
async def support_handler(message: Message):
    await message.answer(
        "Контакты разработчика:\n"
        "@tigraut (или твой @username)\n\n"
        "Напиши мне в ЛС — отвечу максимально быстро.",
        reply_markup=support_kb
    )

# ==================== СОБЕСЕДНИК ====================
@dp.message(F.text == "Собеседник")
async def companion_start(message: Message):
    user_id = message.from_user.id
    await reset_all_modes(user_id)
    await set_user_mode(user_id, "companion_mode", 1)
    await message.answer(
        "Собеседник активирован! Теперь болтаем ТОЛЬКО про футбол на британском английском.\n"
        "Пиши что угодно — я отвечу как фанат из Манчестера.\n"
        "Выход: /exit",
        reply_markup=main_menu
    )

# ==================== СЛОВАРЬ ====================
@dp.message(F.text == "Словарь")
async def dictionary_start(message: Message):
    user_id = message.from_user.id
    await reset_all_modes(user_id)
    await set_user_mode(user_id, "dictionary_mode", 1)
    await message.answer(
        "Словарь футбольных терминов активирован!\n"
        "Пиши слово на русском или английском (например: «offside» или «вне игры»)",
        reply_markup=main_menu
    )

# ==================== НОВОСТИ ====================
@dp.message(F.text == "Новости")
async def news_start(message: Message):
    user_id = message.from_user.id
    await reset_all_modes(user_id)
    await set_user_mode(user_id, "news_mode", 1)
    await message.answer("Загружаю свежие новости футбола с BBC...", reply_markup=main_menu)
    summary = await get_football_news()
    await message.answer(summary, reply_markup=continue_kb)

# ==================== ВЫХОД ====================
@dp.message(Command("exit"))
async def exit_command(message: Message):
    await reset_all_modes(message.from_user.id)
    await message.answer("Ты вышел из режима. Возвращаемся в меню.", reply_markup=main_menu)

# ==================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ====================
@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    state = await get_user_state(user_id)

    if state.get("companion_mode") == 1:
        answer = await get_companion_response(user_id, message.text)
        await message.answer(answer)

    elif state.get("dictionary_mode") == 1:
        answer = await get_dictionary_response(message.text)
        await message.answer(answer, reply_markup=continue_kb)

    elif state.get("news_mode") == 1:
        await message.answer("Новости уже загружены. Пиши новое ключевое слово или нажми «Продолжить поиск»", reply_markup=continue_kb)
    else:
        await message.answer("Используй кнопки меню ниже 👇", reply_markup=main_menu)

# ==================== CALLBACK КНОПКИ ====================
@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery):
    await reset_all_modes(callback.from_user.id)
    await callback.message.edit_text("Возвращаемся в главное меню", reply_markup=None)
    await callback.message.answer("Выбери режим:", reply_markup=main_menu)
    await callback.answer()

@dp.callback_query(F.data == "continue")
async def continue_search(callback: CallbackQuery):
    await callback.answer("Режим всё ещё активен — просто пиши слово или тему!")

# ==================== ЗАПУСК ====================
async def main():
    await init_db()
    print("Бот запущен — сдавай на отлично!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
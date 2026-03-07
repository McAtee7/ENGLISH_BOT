
import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from DB import init_db, get_user_state, set_user_mode, set_user_role, reset_all_modes, save_user_info
from keyboards import main_menu, continue_kb, support_kb, companion_role_kb
from moderation import handle_moderation
from companion import get_companion_response
from dictionary import get_dictionary_response
from news import get_football_news

load_dotenv()
GROQ_KEY = os.getenv("")  # используется в других файлах через litellm

bot = Bot(token="")
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await save_user_info(
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.last_name,
        message.from_user.username,
        message.from_user.language_code
    )
    await message.answer(
        "Привет, mate! Я твой британский футбольный бот для практики английского.\n"
        "Выбирай режим кнопками ниже 👇",
        reply_markup=main_menu
    )

@dp.message(F.text == "Поддержка")
async def support_handler(message: Message):
    await message.answer("Контакты разработчика:\n@*\nНапиши мне в ЛС — отвечу максимально быстро.", reply_markup=support_kb)

@dp.message(F.text == "Собеседник")
async def companion_start(message: Message):
    await reset_all_modes(message.from_user.id)
    await message.answer("Выберите с кем хотите поговорить:", reply_markup=companion_role_kb)

@dp.message(F.text == "Словарь")
async def dictionary_start(message: Message):
    await reset_all_modes(message.from_user.id)
    await set_user_mode(message.from_user.id, "dictionary_mode", 1)
    await message.answer("Словарь активирован!\nПиши слово на русском или английском.", reply_markup=main_menu)

@dp.message(F.text == "Новости")
async def news_start(message: Message):
    await reset_all_modes(message.from_user.id)
    await set_user_mode(message.from_user.id, "news_mode", 1)
    await message.answer("Загружаю свежие новости футбола...", reply_markup=main_menu)
    summary = await get_football_news()
    await message.answer(summary, reply_markup=continue_kb)

@dp.message(Command("exit"))
async def exit_command(message: Message):
    await reset_all_modes(message.from_user.id)
    await message.answer("Ты вышел из режима. Возвращаемся в меню.", reply_markup=main_menu)

@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    state = await get_user_state(user_id)

    # МОДЕРАЦИЯ
    mod_response = await handle_moderation(user_id, message.text)
    if mod_response:
        await message.answer(mod_response)
        return

    if state.get("companion_mode") == 1:
        generating = await message.answer("Генерирую ответ...")
        try:
            answer = await get_companion_response(user_id, message.text)
            await message.answer(answer)
        finally:
            await generating.delete()

    elif state.get("dictionary_mode") == 1:
        generating = await message.answer("Генерирую ответ...")
        try:
            answer = await get_dictionary_response(message.text)
            await message.answer(answer, reply_markup=continue_kb)
        finally:
            await generating.delete()

    elif state.get("news_mode") == 1:
        await message.answer("Вот последние новости...")
    else:
        await message.answer("Используй кнопки меню ниже 👇", reply_markup=main_menu)

@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery):
    await reset_all_modes(callback.from_user.id)
    await callback.message.edit_text("Возвращаемся в главное меню", reply_markup=None)
    await callback.message.answer("Выбери режим:", reply_markup=main_menu)
    await callback.answer()

@dp.callback_query(F.data == "continue")
async def continue_search(callback: CallbackQuery):
    await callback.answer("Режим активен — просто пиши!")
@dp.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery):
    text = """Правила использования бота ENGLISH_BOT

Бот только для практики английского.
Запрещено: джейлбрейк, запрос промптов, кода, API и т.д.
За нарушение — бан.
Все данные только для работы бота."""
    await callback.message.edit_text(text, reply_markup=support_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("role_"))
async def set_companion_role(callback: CallbackQuery):
    user_id = callback.from_user.id
    role = "teammate" if callback.data == "role_teammate" else "coach"
    await set_user_role(user_id, role)
    await set_user_mode(user_id, "companion_mode", 1)

    role_name = "Сокомандник" if role == "teammate" else "Тренер"
    await callback.message.edit_text(
        f"✅ Режим {role_name} активирован!\n\nТеперь пиши мне что угодно на английском, mate! ⚽️",
        reply_markup=None
    )
    await callback.answer()

async def main():
    await init_db()
    print("✅ Бот запущен — сдавай на отлично!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
load_dotenv()

from database import (
    create_request as create_request_in_db,
    get_user_requests,
    init_db,
    update_request_status,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
STATUS_LABELS = {
    "new": "🆕 Новая",
    "in_progress": " 🟡 В работе",
    "done": "✅ Выполнено",
    "cancelled": "❌ Отменено",
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class RequestForm(StatesGroup):
    task = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=" 📩 Оставить заявку")],
        [KeyboardButton(text=" 📋 Мои заявки")],
        [KeyboardButton(text="🛠 Услуги"), KeyboardButton(text=" 📞 Контакты")],
    ],
    resize_keyboard=True,
)

def request_status_keyboard(request_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="В работу",
                    callback_data=f"status:{request_id}:in_progress",
                ),
                InlineKeyboardButton(
                    text="Выполнено",
                    callback_data=f"status:{request_id}:done",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data=f"status:{request_id}:cancelled",
                )
            ],
        ]
    )
@dp.message(lambda message: message.text == "📋 Мои заявки")
async def show_my_requests(message: Message):
    requests = get_user_requests(message.from_user.id)

    if not requests:
        await message.answer("У вас пока нет заявок.")
        return

    text = "Ваши последние заявки:\n\n"

    for request_id, task, status, created_at in requests:
        status_label = STATUS_LABELS.get(status, status)

        text += (
            f"#{request_id}\n"
            f"Задача: {task}\n"
            f"Статус: {status_label}\n"
            f"Создана: {created_at}\n\n"
        )


    await message.answer(text)

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Я бот для обработки заявок.\n\n"
        "Что можно делать:\n"
        "— Оставить заявку\n"
        "— посмотреть свои заявки\n"
        "— узнать список услуг\n"
        "— получить Контакты\n\n"
        "После создания заявки администратор может менять её статус: "
        "новая, в работе, выполнена или отменена."
    )

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я бот для обработки заявок.",
        reply_markup=main_keyboard,
    )


@dp.message(lambda message: message.text == " 📩 Оставить заявку")
async def start_request_form(message: Message, state: FSMContext):
    await state.set_state(RequestForm.task)
    await message.answer("Опишите, что нужно сделать.")


@dp.message(RequestForm.task)
async def get_task(message: Message, state: FSMContext):
    task = message.text
    user = message.from_user

    username = f"@{user.username}" if user.username else "username не указан"

    try:
        request_id = create_request_in_db(
            user_id=user.id,
            username=username,
            full_name=user.full_name,
            task=task,
        )

        admin_text = (
            f"Новая заявка #{request_id}\n\n"
            f"Задача: {task}\n\n"
            f"Пользователь: {user.full_name}\n"
            f"Username: {username}\n"
            f"User ID: {user.id}\n"
            f"Статус: {STATUS_LABELS['new']}"
        )

        await bot.send_message(
            CHANNEL_ID,
            admin_text,
            reply_markup=request_status_keyboard(request_id),
        )

    except Exception as error:
        print(f"Ошибка при создании заявки: {error}")

        await message.answer(
            "Не получилось отправить заявку. Попробуйте позже."
        )
        await state.clear()
        return

    await message.answer("Заявка отправлена. Скоро с вами свяжутся.")
    await state.clear()


@dp.callback_query(lambda callback: callback.data.startswith("status:"))
async def change_request_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "У вас нет прав менять статус заявки.",
            show_alert=True,
        )
        return

    _, request_id, status = callback.data.split(":")

    update_request_status(
        request_id=int(request_id),
        status=status,
    )

    await callback.answer("Статус обновлён")

    old_text = callback.message.text
    lines = old_text.splitlines()
    updated_lines = []

    for line in lines:
        if line.startswith("Статус:"):
            updated_lines.append(f"Статус: {STATUS_LABELS.get(status, status)}")
        else:
            updated_lines.append(line)

    new_text = "\n".join(updated_lines)

    await callback.message.edit_text(
        new_text,
        reply_markup=request_status_keyboard(request_id),
    )

@dp.message()
async def handle_message(message: Message):
    if message.text == "🛠 Услуги":
        await message.answer(
            "🛠 Услуги:\n\n"
            "1. Telegram-боты\n"
            "2. Python-скрипты\n"
            "3. Автоматизация задач\n"
            "4. Backend-сервисы"
        )

    elif message.text == "📞 Контакты":
        await message.answer("Telegram: *******")

    else:
        await message.answer("Выберите действие из меню.")


async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
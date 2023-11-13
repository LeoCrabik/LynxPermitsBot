# handlers/handlers.py
from aiogram import types
from bot import dp
import re
from keyboard import previous_data
from storage.data_handler import save_to_json, read_json

# Словарь для хранения временных данных пользователей
user_data = {}


@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    username = message.from_user.username
    if username:
        filename = f"{username}.json"
    user_data[message.from_user.id] = read_json(filename)
    await message.answer("Hi!\n\nWhat is your name?", reply_markup=previous_data(user_data[message.from_user.id]['name']))
    user_data[message.from_user.id]['state'] = 'name'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'name')
async def process_name(message: types.Message):
    user_data[message.from_user.id]['name'] = message.text
    await message.answer(f"Good job, {user_data[message.from_user.id]['name']}! Enter the phone number.", reply_markup=previous_data(user_data[message.from_user.id]['phone']))
    user_data[message.from_user.id]['state'] = 'phone'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'phone')
async def process_phone(message: types.Message):
    if (len(message.text) < 10) or (not message.text[0:].isdigit() and not re.fullmatch(r'\d\d\d-\d\d\d-\d\d\d\d', message.text)):
        await message.answer("Enter the correct phone number please (for example: 123-456-7890 or 1234567890).")
        return
    user_data[message.from_user.id]['phone'] = message.text
    await message.answer("Thanks! Enter your e-mail.", reply_markup=previous_data(user_data[message.from_user.id]['email']))
    user_data[message.from_user.id]['state'] = 'email'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'email')
async def process_email(message: types.Message):
    if not re.fullmatch('\w+@\w+.\w+', message.text):
        await message.answer("Enter the correct e-mail please.")
        return
    user_data[message.from_user.id]['email'] = message.text

    # Сохраняем данные в JSON файл
    username = message.from_user.username
    if username:
        # Создаем имя файла на основе имени пользователя
        filename = f"{username}.json"
        # Сохраняем данные в JSON файл с именем пользователя
        save_to_json(user_data[message.from_user.id], filename)

    await message.answer("Your answers was saved")

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def permit_types():
    types_list = ['Oversize', 'Overweight', 'Both']
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in types_list:
        kb.add(KeyboardButton(item))
    kb.add(KeyboardButton('/cancel'))
    return kb


def how_is_it_loaded():
    types_list = ['End-to-End', 'Stacked', 'Single Item', 'Side-by-Side']
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in types_list:
        kb.add(KeyboardButton(item))
    kb.add(KeyboardButton('/cancel'))
    return kb


def previous_data(text, cancel_button=True):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton(text))
    if cancel_button:
        kb.add(KeyboardButton('/cancel'))
    return kb


def start_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('/start'))
    return kb


def cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('/cancel'))
    return kb


def confirmation_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in ['Send data', 'Start again']:
        kb.add(KeyboardButton(item))
    kb.add(KeyboardButton('/cancel'))
    return kb


def companies_kb(names_list):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in names_list:
        kb.add(KeyboardButton(item))
    return kb


def take_permit_kb():
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Take order", callback_data='take_permit')
    markup.add(button)
    return markup


def trlr_dimension_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in ['48', '53']:
        kb.add(KeyboardButton(item))
    kb.add(KeyboardButton('/cancel'))
    return kb


def trlr_type_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in ['RGN', 'Stepdeck', 'Flatbed']:
        kb.add(KeyboardButton(item))
    kb.add(KeyboardButton('/cancel'))
    return kb


def format_date(date):
    date_list = date.split('/')
    date = f'{date_list[0]}/{date_list[1]}/20{date_list[2]}'
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton(date))
    return kb

# handlers/handlers.py
from aiogram import types
from bot import dp, bot
import re
from keyboard import *
from storage.data_handler import save_to_json, read_json, save_to_excel, read_questions, find_jsons
from datetime import date, datetime
import json

# Словарь для хранения временных данных пользователей
user_data = {}
states = [item['var_name'] for item in read_questions()]


# def bot_answer(message: types.Message, answer_text, reply_markup, new_state):
#     await message.answer(answer_text, reply_markup=reply_markup)
#     user_data[message.from_user.id]['state'] = new_state


@dp.message_handler(commands=['cancel'])
async def on_cancel(message: types.Message):
    current_state = user_data[message.from_user.id]['state']
    if current_state == 'confirmation':
        state_id = states.index('comment') + 1
    else:
        state_id = states.index(current_state)
    if state_id == 0:
        return
    user_data[message.from_user.id]['state'] = states[state_id - 1]
    if user_data[message.from_user.id]['state'] == 'date':
        await message.answer("Enter was canceled. Enter the corrected data", reply_markup=format_date(
            user_data[message.from_user.id][user_data[message.from_user.id]['state']]))
    elif user_data[message.from_user.id]['state'] == 'permit_type':
        await message.answer("Enter was canceled. Enter the corrected data", reply_markup=permit_types())
    elif user_data[message.from_user.id]['state'] == 'permit_type':
        await message.answer("Enter was canceled. Enter the corrected data", reply_markup=how_is_it_loaded())
    elif user_data[message.from_user.id]['state'] == 'applicant_company':
        username = message.from_user.username
        if username:
            company_names = []
            company_files = find_jsons(username)
            for file_path in company_files:
                with open(f'data/user_data/{file_path}') as file:
                    data = json.load(file)
                    company_names.append(data['applicant_company'])
        await message.answer("Enter the <b>COMPANY NAME</b>",
                             reply_markup=companies_kb(company_names), parse_mode="HTML")
    else:
        await message.answer("Enter was canceled. Enter the corrected data", reply_markup=previous_data(
            user_data[message.from_user.id][user_data[message.from_user.id]['state']]))


@dp.callback_query_handler(lambda query: query.data == 'take_permit')
async def take_permit(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id  # Получаем ID пользователя, который нажал на кнопку

    # Создаем новый текст с информацией о взятии "permit"
    new_message_text = f"Started working on the order: @{callback_query.from_user.username}"

    # Отправляем новое сообщение как ответ на предыдущее сообщение с файлом
    await bot.send_message(chat_id=callback_query.message.chat.id, text=new_message_text,
                           reply_to_message_id=callback_query.message.message_id)
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id, reply_markup=None)


@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    if message.chat.id == -4087172229:
        return
    # await bot.send_message(text=f'@{message.from_user.username} - {message.from_user.id}', chat_id='-4087172229')
    username = message.from_user.username
    if username:
        company_names = []
        company_files = find_jsons(username)
        for file_path in company_files:
            with open(f'data/user_data/{file_path}') as file:
                data = json.load(file)
                company_names.append(data['applicant_company'])
        # filename = f"{username}.json"
        # for item in find_jsons(username):
        #     await message.answer(item)
    # user_data[message.from_user.id] = read_json(filename)
    await message.answer("Bot was started", reply_markup=types.ReplyKeyboardRemove())
    print(message.chat.id)
    await message.answer("Enter the <b>COMPANY NAME</b>",
                         reply_markup=companies_kb(company_names), parse_mode="HTML")
    user_data[message.from_user.id] = {}
    user_data[message.from_user.id]['state'] = 'applicant_company'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'applicant_company')
async def process_applicant_company(message: types.Message):
    if len(message.text) < 2:
        await message.answer('Enter the correct company name')
        return
    user_data[message.from_user.id] = read_json(
        f'{message.from_user.username}_{re.sub(r"[^A-Za-z0-9]+", "", message.text)}.json')
    user_data[message.from_user.id]['applicant_company'] = message.text
    await message.answer('Enter the <b>DOT NUMBER</b>',
                         reply_markup=previous_data(user_data[message.from_user.id]['dot_number']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'dot_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'dot_number')
async def process_dot_number(message: types.Message):
    if len(message.text) < 1 and not message.text[0:].isdigit():
        await message.answer('Enter the correct DOT number')
        return
    user_data[message.from_user.id]['dot_number'] = message.text
    await message.answer('Enter <b>PERMIT START DATE</b>',
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'date'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'date')
async def process_dot_number(message: types.Message):
    if not re.fullmatch(
            r'^(?:(?:0[1-9]|1[0-2])(\/|-|\.)\d{2}\1\d{4})$',
            message.text
    ) or not (str(datetime.now().year + 1) >= re.split('\D', str(message.text))[2] >= str(datetime.now().year)):
        await message.answer('Enter the correct date (mm/dd/yyyy, mm-dd-yyyy or mm.dd.yyyy)')
        return
    user_date = re.split('\D', message.text)
    user_date = [user_date[1], user_date[0], user_date[2]]
    user_date = (int(item if len(item) > 1 else f'0{item}') for item in user_date[::-1])
    try:
        user_data[message.from_user.id]['date'] = datetime(*user_date).strftime("%m/%d/%y")
    except Exception as e:
        await message.answer('Enter the correct date (mm/dd/yyyy, mm-dd-yyyy or mm.dd.yyyy)')
        return
    await message.answer('Enter your <b>FULL NAME</b> (first name and last name)',
                         reply_markup=previous_data(user_data[message.from_user.id]['contact_name']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'contact_name'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'contact_name')
async def process_name(message: types.Message):
    if not len(message.text.split(' ')) > 1:
        await message.answer('Enter the correct full name (first name and last name)')
        return
    user_data[message.from_user.id]['contact_name'] = message.text
    await message.answer(f"Enter your <b>PHONE NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['contact_phone']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'contact_phone'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'contact_phone')
async def process_phone(message: types.Message):
    patterns = [
        r'^\d{3}-\d{3}-\d{4}$',
        r'^\d{10}$',
        r'^\d{3} \d{3} \d{4}$',
        r'^\d-\d{3}-\d{3}-\d{4}$',
        r'^\(\d{3}\) \d{3}-\d{4}$',
        r'^\d{3}-\d{3}-\d{4}$',
        r'^\d{3} \d{3} \d{4}$',
        r'^\(\d{3}\) \d{3}-\d{4}$'
    ]
    if not any(re.fullmatch(pattern, message.text) for pattern in patterns):
        await message.answer("Enter the correct phone number please (for example: 123-456-7890 or 1234567890 or (123) 123-1234 or 123 123 1234")
        return
    user_data[message.from_user.id]['contact_phone'] = message.text
    await message.answer("Enter your <b>EMAIL</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['contact_email']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'contact_email'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'contact_email')
async def process_email(message: types.Message):
    if not re.fullmatch('\w+@\w+.\w+', message.text):
        await message.answer("Enter the correct email please")
        return
    user_data[message.from_user.id]['contact_email'] = message.text
    await message.answer("Enter the <b>FEDERAL ID NUMBER</b>",
                         reply_markup=previous_data(
                             user_data[message.from_user.id]['federal_id']) if user_data[message.from_user.id][
                             'federal_id'] else previous_data("None"), parse_mode="HTML"
                         )
    user_data[message.from_user.id]['state'] = 'federal_id'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'federal_id')
async def process_federal_id(message: types.Message):
    if message.text == "None":
        user_data[message.from_user.id]['federal_id'] = ""
    elif len(message.text) < 1:
        await message.answer("Enter the correct federal ID number")
        return
    else:
        user_data[message.from_user.id]['federal_id'] = message.text
    await message.answer("Choose <b>PERMIT TYPE</b>", reply_markup=permit_types(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'permit_type'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'permit_type')
async def process_permit_type(message: types.Message):
    if not message.text in ['Oversize', 'Overweight', 'Both']:
        await message.answer("Choose the correct permit type")
        return
    user_data[message.from_user.id]['permit_type'] = message.text
    await message.answer("Enter the <b>APPLICATION LOAD/PRO NUMBER</b> (optional)", reply_markup=previous_data("None"), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'application_load_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'application_load_number')
async def process_application_load_number(message: types.Message):
    if message.text == "None":
        user_data[message.from_user.id]['application_load_number'] = ""
    elif len(message.text) < 1:
        await message.answer("Enter the correct application load/pro number")
        return
    else:
        user_data[message.from_user.id]['application_load_number'] = message.text
    await message.answer("Enter <b>START ADDRESS</b>", reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'start_address'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'start_address')
async def process_start_address(message: types.Message):
    if len(message.text) < 5:
        await message.answer("Enter the correct address")
        return
    user_data[message.from_user.id]['start_address'] = message.text
    await message.answer("Enter the <b>DESTINATION ADDRESS</b>", reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'destination_address'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'destination_address')
async def process_destination_address(message: types.Message):
    if len(message.text) < 5:
        await message.answer("Enter the correct address")
        return
    user_data[message.from_user.id]['destination_address'] = message.text
    await message.answer("Enter the <b>TRACTOR NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_number']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_number')
async def process_tractor_number(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct tractor number")
        return
    user_data[message.from_user.id]['tractor_number'] = message.text
    await message.answer("Enter the <b>TRACTOR YEAR</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_year']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_year'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_year')
async def process_tractor_year(message: types.Message):
    if not (len(message.text) == 4 and message.text[0:].isdigit() and (
            str(datetime.now().year + 1) >= message.text >= str(1950))):
        await message.answer("Enter the correct tractor year")
        return
    user_data[message.from_user.id]['tractor_year'] = message.text
    await message.answer("Enter the <b>TRACTOR MAKE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_make']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_make'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_make')
async def process_tractor_make(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct tractor make")
        return
    user_data[message.from_user.id]['tractor_make'] = message.text
    await message.answer("Enter the <b>TRACTOR LICENSE PLATE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_license']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_license'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_license')
async def process_tractor_license(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct tractor license plate")
        return
    user_data[message.from_user.id]['tractor_license'] = message.text
    await message.answer("Enter the <b>TRACTOR PLATE STATE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_state']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_state'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_state')
async def process_tractor_state(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct tractor plate state")
        return
    user_data[message.from_user.id]['tractor_state'] = message.text
    await message.answer("Enter the <b>TRACTOR VIN NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_sn']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_sn'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_sn')
async def process_tractor_sn(message: types.Message):
    if not len(message.text) == 17:
        await message.answer("Enter the correct VIN number")
        return
    user_data[message.from_user.id]['tractor_sn'] = message.text
    await message.answer("Enter the <b>TRACTOR AXLES NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['tractor_axles_number']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'tractor_axles_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'tractor_axles_number')
async def process_tractor_axles_number(message: types.Message):
    if not (message.text[0:].isdigit() and 2 <= int(message.text) <= 5):
        await message.answer("Enter the correct tractor axles number")
        return
    user_data[message.from_user.id]['tractor_axles_number'] = message.text
    await message.answer("Enter the <b>TRAILER NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_number']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_number')
async def process_trailer_number(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct trailer number")
        return
    user_data[message.from_user.id]['trailer_number'] = message.text
    await message.answer("Enter the <b>TRAILER YEAR</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_year']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_year'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_year')
async def process_trailer_year(message: types.Message):
    if not (len(message.text) == 4 and message.text[0:].isdigit() and (
            str(datetime.now().year + 1) >= message.text >= str(1950))):
        await message.answer("Enter the correct trailer year")
        return
    user_data[message.from_user.id]['trailer_year'] = message.text
    await message.answer("Enter the <b>TRAILER DIMENSION</b>",
                         reply_markup=trlr_dimension_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_dimension'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_dimension')
async def process_trailer_dimension(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct dimension year")
        return
    user_data[message.from_user.id]['trailer_dimension'] = message.text
    await message.answer("Enter the <b>TRAILER TYPE</b>", reply_markup=trlr_type_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_type'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_type')
async def process_trailer_type(message: types.Message):
    if message.text == "None":
        user_data[message.from_user.id]['trailer_type'] = ""
    elif len(message.text) < 1:
        await message.answer("Enter the correct trailer type")
        return
    else:
        user_data[message.from_user.id]['trailer_type'] = message.text
    await message.answer("Enter the <b>TRAILER MAKE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_make']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_make'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_make')
async def process_trailer_make(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct trailer make")
        return
    user_data[message.from_user.id]['trailer_make'] = message.text
    await message.answer("Enter the <b>TRAILER LICENSE PLATE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_license']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_license'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_license')
async def process_trailer_license(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct trailer license plate")
        return
    user_data[message.from_user.id]['trailer_license'] = message.text
    await message.answer("Enter the <b>TRAILER PLATE STATE</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_state']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_state'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_state')
async def process_trailer_sn(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct trailer plate state")
        return
    user_data[message.from_user.id]['trailer_state'] = message.text
    await message.answer("Enter the <b>TRAILER VIN NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_sn']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_sn'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_sn')
async def process_trailer_state(message: types.Message):
    if not len(message.text) == 17:
        await message.answer("Enter the correct VIN number")
        return
    user_data[message.from_user.id]['trailer_sn'] = message.text
    await message.answer("Enter the <b>TRAILER AXLES NUMBER</b>",
                         reply_markup=previous_data(user_data[message.from_user.id]['trailer_axles_number']), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'trailer_axles_number'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'trailer_axles_number')
async def process_trailer_axles_number(message: types.Message):
    if not (message.text[0:].isdigit() and 2 <= int(message.text) <= 5):
        await message.answer("Enter the correct trailer axles number")
        return
    user_data[message.from_user.id]['trailer_axles_number'] = message.text
    await message.answer("Enter the <b>DESCRIPTION OF LOAD</b>", reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_description'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_description')
async def process_load_description(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct description of load")
        return
    user_data[message.from_user.id]['load_description'] = message.text
    await message.answer("Enter <b>LOAD NO. OF PIECES</b>", reply_markup=previous_data('None'), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'number_of_pieces'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'number_of_pieces')
async def process_number_of_pieces(message: types.Message):
    if message.text == "None":
        user_data[message.from_user.id]['number_of_pieces'] = ""
    elif len(message.text) < 1 or not message.text[0:].isdigit():
        await message.answer("Enter the correct No. of pieces")
        return
    else:
        user_data[message.from_user.id]['number_of_pieces'] = message.text
    await message.answer("Enter <b>LOAD MACHINERY MAKE</b> (None if not machinery)", reply_markup=previous_data('None'), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_machinery_make'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_machinery_make')
async def process_load_machinery_make(message: types.Message):
    if message.text == "None":
        user_data[message.from_user.id]['load_machinery_make'] = ""
    elif len(message.text) < 1:
        await message.answer("Enter the correct machinery make (None if not machinery)")
        return
    else:
        user_data[message.from_user.id]['load_machinery_make'] = message.text
    await message.answer("Enter <b>LOAD MODEL</b>", reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_model'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_model')
async def process_load_model(message: types.Message):
    if len(message.text) < 1:
        await message.answer("Enter the correct model")
        return
    user_data[message.from_user.id]['load_model'] = message.text
    await message.answer("Enter <b>LOAD SERIAL NUMBER</b>", reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_sn'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_sn')
async def process_load_sn(message: types.Message):
    if len(message.text) < 3:
        await message.answer("Enter the correct load serial number", reply_markup=previous_data('None'))
        return
    user_data[message.from_user.id]['load_sn'] = message.text

    if user_data[message.from_user.id]['permit_type'] in ['Overweight', 'Both']:
        await message.answer("Enter the <b>LOAD WEIGHT</b> (in lbs.)", reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'load_weight'
    else:
        await message.answer("Enter the <b>LOAD HEIGHT</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                             reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'load_height'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_weight')
async def process_load_weight(message: types.Message):
    if not re.fullmatch(r'^(?:\d{5,}|\d{5,}[.,]\d+)$', message.text):
        await message.answer("Enter the correct load weight (in lbs.)")
        return
    user_data[message.from_user.id]['load_weight'] = message.text
    if user_data[message.from_user.id]['permit_type'] in ['Oversize', 'Both']:
        await message.answer("Enter the <b>LOAD HEIGHT</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                             reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'load_height'
    else:
        await message.answer("Enter the <b>OVERALL WEIGHT</b> (in lbs.)", reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'total_weight'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_height')
async def process_load_height(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct load height in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['load_height'] = message.text
    await message.answer("Enter the <b>LOAD WIDTH</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_width'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_width')
async def process_load_width(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct load width in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['load_width'] = message.text
    await message.answer("Enter the <b>LOAD LENGTH</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'load_length'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'load_length')
async def process_load_length(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct load length in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['load_length'] = message.text

    if user_data[message.from_user.id]['permit_type'] in ['Overweight', 'Both']:
        await message.answer("Enter the <b>OVERALL WEIGHT</b> (in lbs.)", reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'total_weight'
    else:
        await message.answer(
            "Enter the overall height in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
            reply_markup=cancel_kb())
        user_data[message.from_user.id]['state'] = 'total_height'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'total_weight')
async def process_total_weight(message: types.Message):
    if not re.fullmatch(r'^(?:\d{5,}|\d{5,}[.,]\d+)$', message.text):
        await message.answer("Enter the correct total weight (in lbs.)")
        return
    user_data[message.from_user.id]['total_weight'] = message.text
    if user_data[message.from_user.id]['permit_type'] in ['Oversize', 'Both']:
        await message.answer(
            "Enter the <b>OVERALL HEIGHT</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
            reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'total_height'
    else:
        await message.answer("Choose <b>HOW IS IT LOADED</b>", reply_markup=how_is_it_loaded(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'how_is_it_loaded'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'total_height')
async def process_total_height(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct overall height in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['total_height'] = message.text
    await message.answer("Enter the <b>OVERALL WIDTH</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'total_width'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'total_width')
async def process_total_width(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text) or not int(
            re.split(r'\D+', message.text)[0]) >= 8:
        await message.answer(
            "Enter the correct overall width in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['total_width'] = message.text
    await message.answer("Enter the <b>OVERALL LENGTH</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'total_length'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'total_length')
async def process_total_length(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct overall length in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['total_length'] = message.text
    await message.answer("Enter the <b>OVERHANG FRONT</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'overhang_front'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'overhang_front')
async def process_overhang_front(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct overhang front in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['overhang_front'] = message.text
    await message.answer("Enter the <b>OVERHANG REAR</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)",
                         reply_markup=cancel_kb(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'overhang_rear'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'overhang_rear')
async def process_overhang_rear(message: types.Message):
    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            "Enter the correct overhang rear in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id]['overhang_rear'] = message.text
    await message.answer("Choose <b>HOW IS IT LOADED</b>", reply_markup=how_is_it_loaded(), parse_mode="HTML")
    user_data[message.from_user.id]['state'] = 'how_is_it_loaded'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'how_is_it_loaded')
async def process_how_is_it_loaded(message: types.Message):
    if not message.text in ['End-to-End', 'Stacked', 'Single Item', 'Side-by-Side']:
        await message.answer("Choose the correct option")
        return
    user_data[message.from_user.id]['how_is_it_loaded'] = message.text
    if user_data[message.from_user.id]['permit_type'] != 'Oversize':
        await message.answer(
            "Enter the <b>AXLE #1 WEIGHT</b> in lbs",
            reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'axle1_weight'
    else:
        await message.answer(
            'Enter the <b>AXLE #1 SPACINGS</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)',
            reply_markup=previous_data(user_data[message.from_user.id]['axle1_spacings']), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'axle1_spacings'


##################################################
# @dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'number_of_axles')
# async def process_number_of_axles(message: types.Message):
#     if not (message.text[0:].isdigit() and 2 <= int(message.text) <= 12):
#         await message.answer("Enter the correct number of axles")
#         return
#     user_data[message.from_user.id]['number_of_axles'] = message.text
#     if user_data[message.from_user.id]['permit_type'] != 'Overweight':
#         await message.answer('Enter the axle #1 spacings in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)',reply_markup=previous_data(user_data[message.from_user.id]['axle1_spacings']))
#         user_data[message.from_user.id]['state'] = 'axle1_spacings'
#     else:
#         await message.answer(
#             "Enter the axle #1 weight in lbs",
#             reply_markup=cancel_kb())
#         user_data[message.from_user.id]['state'] = 'axle1_weight'
##################################################


@dp.message_handler(lambda message: re.fullmatch(r'axle\d+_weight', user_data[message.from_user.id]['state']))
async def process_axles_weight(message: types.Message):
    axle_number = int(re.search(r'\d+', user_data[message.from_user.id]['state']).group())

    if not re.fullmatch(r'^(?:\d{4,}|\d{4,}[.,]\d+)$', message.text):
        await message.answer(f"Enter the correct axle #{axle_number} weight in lbs")
        return
    user_data[message.from_user.id][f'axle{axle_number}_weight'] = message.text
    if axle_number == int(user_data[message.from_user.id]['tractor_axles_number']) + int(
            user_data[message.from_user.id]['trailer_axles_number']):
        await message.answer(
            "Please enter <b>YOUR COMMENTS</b> below, any additional information, Google Maps Link, or any other information that may be helpful",
            reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'comment'
    else:
        reply_markup = previous_data(
            user_data[message.from_user.id][f'axle{axle_number}_spacings']) if axle_number <= int(
            user_data[message.from_user.id]['tractor_axles_number']) else cancel_kb()
        await message.answer(
            f'Enter the <b>AXLE #{axle_number} SPACINGS</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)',
            reply_markup=reply_markup, parse_mode="HTML")
        user_data[message.from_user.id]['state'] = f'axle{axle_number}_spacings'


@dp.message_handler(lambda message: re.fullmatch(r'axle\d+_spacings', user_data[message.from_user.id]['state']))
async def process_axles_spacings(message: types.Message):
    axle_number = int(re.search(r'\d+', user_data[message.from_user.id]['state']).group())

    if not re.fullmatch(r'\d+(?:[\.\-\'\s"]\d+)?(?:\")?', message.text):
        await message.answer(
            f"Enter the correct axle #{axle_number} in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)")
        return
    user_data[message.from_user.id][f'axle{axle_number}_spacings'] = message.text
    if user_data[message.from_user.id]['permit_type'] != 'Oversize':
        await message.answer(f'Enter the <b>AXLE #{axle_number + 1} WEIGHT</b> in lbs', reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = f'axle{axle_number + 1}_weight'
    elif axle_number + 1 == int(user_data[message.from_user.id]['tractor_axles_number']) + int(
            user_data[message.from_user.id]['trailer_axles_number']):
        await message.answer(
            "Please enter <b>YOUR COMMENTS</b> below, any additional information, Google Maps Link, or any other information that may be helpful",
            reply_markup=cancel_kb(), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'comment'
    else:
        reply_markup = previous_data(
            user_data[message.from_user.id][f'axle{axle_number + 1}_spacings']) if axle_number + 1 <= int(
            user_data[message.from_user.id]['tractor_axles_number']) else cancel_kb()
        await message.answer(
            f'Enter the <b>AXLE #{axle_number + 1} SPACINGS</b> in the format  feet inches (e.g., 10.5 or 10-5 or 10\'5\" or 10)',
            reply_markup=reply_markup, parse_mode="HTML")
        user_data[message.from_user.id]['state'] = f'axle{axle_number + 1}_spacings'


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'comment', content_types=types.ContentTypes.ANY)
async def process_comment(message: types.Message):
    has_photo = bool(message.photo)  # Проверяем наличие фото
    has_document = bool(message.document)  # Проверяем наличие документа (файла)
    has_voice = bool(message.voice)  # Проверяем наличие голосового сообщения
    print(has_photo, has_document, has_voice)
    if has_photo or has_document or has_voice:
        user_data[message.from_user.id]['multimedia'] = message.message_id
        user_data[message.from_user.id]['state'] = 'confirmation'
    elif message.text == "None":
        user_data[message.from_user.id]['comment'] = ""
    elif len(message.text) < 1:
        await message.answer("Enter the correct comment")
        return
    else:
        user_data[message.from_user.id]['comment'] = message.text
    formatted_string = '\n'.join(
        f"{question['name']} {user_data[message.from_user.id][question['var_name']]}" for question in read_questions()
        if user_data[message.from_user.id][question['var_name']])
    await message.answer(formatted_string)
    await message.answer('Check the accuracy of the entered data', reply_markup=confirmation_kb())
    user_data[message.from_user.id]['state'] = 'confirmation'
    username = message.from_user.username
    if username:
        # Сохраняем данные в JSON файл с именем пользователя
        print(user_data[message.from_user.id])
        save_to_json(user_data[message.from_user.id], username,
                     user_data[message.from_user.id]['applicant_company'])


@dp.message_handler(lambda message: user_data[message.from_user.id]['state'] == 'confirmation')
async def process_confirmation(message: types.Message):
    if message.text == "Send data":
        # Сохраняем данные в JSON файл
        username = message.from_user.username
        if username:
            save_to_excel(user_data[message.from_user.id], username)

        await message.answer("Your answers was saved", reply_markup=start_kb())
        await bot.send_message(text=f'Permit ordered by @{username}', chat_id='-4087172229')
        if 'multimedia' in user_data[message.from_user.id]:
            await bot.forward_message(chat_id='-4087172229', from_chat_id=message.chat.id, message_id=user_data[message.from_user.id]['multimedia'])
        await bot.send_document(document=types.InputFile(f'data/output/{username}.xlsx'), chat_id='-4087172229',
                                reply_markup=take_permit_kb())
    elif message.text == "Start again":
        await message.answer("Enter the <b>COMPANY NAME</b>",
                             reply_markup=previous_data(user_data[message.from_user.id]['applicant_company']), parse_mode="HTML")
        user_data[message.from_user.id]['state'] = 'applicant_company'
    else:
        return

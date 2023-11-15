import telebot
import requests
import json
import time
import os
from decouple import config

KEY = config('HOTELS_KEY')
bot = telebot.TeleBot('')
headers = {
    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
    'x-rapidapi-key': KEY
}
city_id = ''
hotels_number = 0
is_photo = False
photo_number = 0
history_record = ''


def search_start(current_bot: telebot, message: telebot.types.Message) -> None:
    """
    Начало поиска
    """
    global history_record
    history_record = '\n{time}'.format(time=time.strftime('%Y-%m-%d %H:%M:%S'))
    global bot
    bot = current_bot
    bot.send_message(message.chat.id, 'Введите название города')
    bot.register_next_step_handler(message, get_city)


def get_city(message: telebot.types.Message) -> None:
    """
    Ввод названия города с проверкой корректности
    """
    city = message.text
    url = "https://hotels4.p.rapidapi.com/locations/search"
    querystring = {'query': city, 'locale': 'ru_RU'}
    req_location = requests.request('GET', url, headers=headers, params=querystring)
    location = json.loads(req_location.text)
    if location['suggestions'][0]['entities']:
        global city_id
        city_id = location['suggestions'][0]['entities'][0]['destinationId']
        bot.send_message(message.chat.id, 'Введите количество показываемых отелей (до 25)')
        bot.register_next_step_handler(message, get_hotels_number)
    else:
        bot.send_message(message.chat.id, 'Города с таким названием нет. Введите другое название города')
        bot.register_next_step_handler(message, get_city)


def get_hotels_number(message: telebot.types.Message) -> None:
    """
    Ввод количества показываемых отелей с проверкой корректности
    """
    global hotels_number
    hotels_number = message.text
    if hotels_number.isdigit() and 1 <= int(hotels_number) <= 25:
        hotels_number = int(hotels_number)
        get_is_photo(message)
    else:
        bot.send_message(message.chat.id, 'Количество отелей должно быть целым числом от 1 до 25')
        bot.register_next_step_handler(message, get_hotels_number)


def get_is_photo(message: telebot.types.Message) -> None:
    """
    Формирование запроса необходимости вывода фото отелей с помощью кнопок
    """
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Да', callback_data='yes'))
    markup.add(telebot.types.InlineKeyboardButton(text='Нет', callback_data='no'))
    bot.send_message(message.chat.id, text='Показать фото каждого отеля?', reply_markup=markup)


def positive_answer(message: telebot.types.Message) -> None:
    """
    Обработка положительного ответа на запрос необходимости вывода фото отелей
    """
    global is_photo
    is_photo = True
    bot.send_message(message.chat.id, 'Введите количество показываемых фото (до 10)')
    bot.register_next_step_handler(message, get_photo_number)


def negative_answer(message: telebot.types.Message) -> None:
    """
    Обработка отрицательного ответа на запрос необходимости вывода фото отелей
    """
    global is_photo
    is_photo = False
    hotels_search(message)


def get_photo_number(message: telebot.types.Message) -> None:
    """
    Ввод количества показываемых фото отелей с проверкой корректности
    """
    global photo_number
    photo_number = message.text
    if photo_number.isdigit() and 1 <= int(photo_number) <= 10:
        photo_number = int(photo_number)
        hotels_search(message)
    else:
        bot.send_message(message.chat.id, 'Количество фото должно быть целым числом от 1 до 10')
        bot.register_next_step_handler(message, get_photo_number)


def hotels_search(message: telebot.types.Message) -> None:
    """
    Получение информации из базы данных
    """
    url = 'https://hotels4.p.rapidapi.com/properties/list'
    global hotels_number
    querystring = {'destinationId': city_id,
                   'pageNumber': '1',
                   'checkIn': time.strftime('%Y-%m-%d'),
                   'checkOut': time.strftime('%Y-%m-%d'),
                   'adults1': '1',
                   'locale': 'ru_RU',
                   'sortOrder': 'PRICE_HIGHEST_FIRST',
                   'pageSize': hotels_number
                   }
    req_hotels = requests.request('GET', url, headers=headers, params=querystring)
    hotels = json.loads(req_hotels.text)
    hotels_output(message, hotels)


def hotels_output(message: telebot.types.Message, hotels: dict) -> None:
    """
    Вывод информации об отелях
    """
    global history_record
    history_record += ' highprice\n{city}'.format(city=hotels['data']['body']['header'])
    bot.send_message(message.chat.id, hotels['data']['body']['header'])
    for i_hotel in hotels['data']['body']['searchResults']['results']:
        if 'name' in i_hotel:
            history_record += '\n{hotel}'.format(hotel=i_hotel['name'])
            bot.send_message(message.chat.id, i_hotel['name'])
        if 'streetAddress' in i_hotel['address']:
            history_record += '\n{address}'.format(address=i_hotel['address']['streetAddress'])
            bot.send_message(message.chat.id, i_hotel['address']['streetAddress'])
        if i_hotel['landmarks'][0]['label'] == 'Центр города':
            history_record += '\n{distance} от центра города'.format(distance=i_hotel['landmarks'][0]['distance'])
            bot.send_message(message.chat.id, i_hotel['landmarks'][0]['distance'] + ' от центра города')
        if 'current' in i_hotel['ratePlan']['price']:
            history_record += '\n{price}'.format(price=i_hotel['ratePlan']['price']['current'])
            bot.send_message(message.chat.id, i_hotel['ratePlan']['price']['current'])
        if is_photo:
            photo_output(message, i_hotel)
    with open(os.path.join('history_files', '{}.txt'.format(message.chat.id)), 'a', encoding='utf-8') as file:
        file.write(history_record)


def photo_output(message: telebot.types.Message, hotel: dict) -> None:
    """
    Вывод фото отелей
    """
    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
    querystring = {'id': hotel['id']}
    req_photos = requests.request('GET', url, headers=headers, params=querystring)
    photos = json.loads(req_photos.text)
    global photo_number
    if len(photos['hotelImages']) > photo_number:
        photos['hotelImages'] = photos['hotelImages'][:photo_number]
    for i_photo in photos['hotelImages']:
        bot.send_photo(message.chat.id, i_photo['baseUrl'].format(size='z'))

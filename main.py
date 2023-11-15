import telebot
from decouple import config
from botrequests import lowprice
from botrequests import highprice
from botrequests import bestdeal
from botrequests import history

TOKEN = config('TELEBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
command = ''


@bot.message_handler(content_types=['text'])
def query(message: telebot.types.Message) -> None:
    """
    Выбор поискового запроса
    """
    command_info = '/lowprice - топ самых дешёвых отелей в городе,' \
                   '\n/highprice - топ самых дорогих отелей в городе,' \
                   '\n/bestdeal - топ отелей, наиболее подходящих по цене и расположению от центра,' \
                   '\n/history - история поиска отелей'
    global command
    if message.text == '/hello_world' or message.text == '/start' or message.text == 'Привет':
        bot.send_message(message.chat.id,
                         'Привет, мы поможем выбрать отель. Выберите необходимый запрос:\n{}'.format(command_info))
    elif message.text == '/help':
        bot.send_message(message.chat.id, command_info)
    elif message.text == '/lowprice':
        command = 'lowprice'
        lowprice.search_start(bot, message)
    elif message.text == '/highprice':
        command = 'highprice'
        highprice.search_start(bot, message)
    elif message.text == '/bestdeal':
        command = 'bestdeal'
        bestdeal.search_start(bot, message)
    elif message.text == '/history':
        history.history_output(bot, message)
    else:
        bot.send_message(message.chat.id, 'Неизвестная команда. Введите /hello_world, /start или Привет.')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call) -> None:
    """
    Обработка запроса необходимости вывода фото отелей с помощью кнопок
    """
    bot.answer_callback_query(callback_query_id=call.id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    if call.data == "yes":
        if command == 'lowprice':
            lowprice.positive_answer(call.message)
        elif command == 'highprice':
            highprice.positive_answer(call.message)
        if command == 'bestdeal':
            bestdeal.positive_answer(call.message)
    else:
        if command == 'lowprice':
            lowprice.negative_answer(call.message)
        elif command == 'highprice':
            highprice.negative_answer(call.message)
        if command == 'bestdeal':
            bestdeal.negative_answer(call.message)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

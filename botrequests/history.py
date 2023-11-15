import telebot
import os

bot = telebot.TeleBot('')


def history_output(current_bot: telebot, message: telebot.types.Message) -> None:
    """
    Вывод истории поиска отелей
    """
    global bot
    bot = current_bot
    try:
        with open(os.path.join('history_files', '{}.txt'.format(message.chat.id)), 'r', encoding='utf-8') as file:
            bot.send_message(message.chat.id, file.read())
    except FileNotFoundError:
        bot.send_message(message.chat.id, 'Поисковые запросы не вводились')

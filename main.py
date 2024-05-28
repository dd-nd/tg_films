from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import sqlite3 as sq
import telebot
from os import getenv
import requests
from urllib.parse import quote
import json

# %20 -- пробел

bot = telebot.TeleBot(getenv('BOT_TOKEN'))
lastMessage = None
headers = {
    "accept": "application/json",
    "X-API-KEY": getenv('API_TOKEN')
}

'''
Функция для получения данных о фильме
'''
def get_data(name):
    url = f"https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=1&query={quote(name)}"
    data = json.loads(requests.get(url, headers=headers).text)

    try:
        data = data['docs'][0]
        json_data = {
            'name': data['name'],
            'alternativeName': data['alternativeName'],
            'countries': data['countries'],
            'year': data['year'],
            'genres': data['genres'],
            'description': data['description'],
            'poster': data['poster']['previewUrl']
        }
        return json_data
    except Exception as e:
        return str(e)
    

'''
Обработчик команды /start для регистрации нового пользователя
'''
@bot.message_handler(commands=['start'])
def start(message: Message):
    with sq.connect('db/database.db') as con: 
        cur = con.cursor()
        cur.execute('INSERT INTO users (user_id, user_name, user_surname, username) VALUES (?, ?, ?, ?) ON CONFLICT (user_id) DO NOTHING',
                    (message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username))
        con.commit()
    bot.send_message( message.chat.id, 'Привет, я бот, который поможет тебе смотреть сериалы.' )


'''
Обработчик команды /add [название] для добавления фильма по названию 
или /add для добавления последнего фильма из поиска по тексту ф. text_searching()
'''
@bot.message_handler(commands=['add'])
def add_item(message):  
    global lastMessage
    if len(message.text) <= 5:
        json_data = get_data(lastMessage)
    elif len(message.text) >= 5:
        try:
            name = message.text.split(' ', 1)[1]
            json_data = get_data(name)
        except IndexError:
            bot.reply_to(message, 'Пожалуйста, введите название фильма.')
        except Exception as e:
            bot.reply_to(message, f'При получении данных произошла ошибка. Пожалуйста, попробуйте снова позже. ❌\n\n{str(e)}')
        
    with sq.connect('db/database.db') as con: 
        cur = con.cursor()
        cur.execute("INSERT INTO items (ru_name, alternative_name, genres, id_user) VALUES (?, ?, ?, ?) ON CONFLICT (ru_name) DO NOTHING", 
                    (json_data['name'], json_data['alternativeName'], json.dumps(json_data['genres'], ensure_ascii=False), message.from_user.id))
        con.commit()
    bot.reply_to(message, f'Фильм успешно добавлен! 🎉')


'''
Обработчик команды /all для вывода всех добавленных фильмов
'''
@bot.message_handler(commands=['all'])
def get_movies_info(message: Message):
    try:
        with sq.connect('db/database.db') as con: 
            cur = con.cursor()
            cur.execute(f'SELECT ru_name FROM items WHERE id_user = {message.from_user.id}')
            results = [res[0] for res in cur.fetchall()]

        if not results:
            bot.send_message(message.chat.id, 'У вас нет ни одного фильма 🤗')
            return
        markup = InlineKeyboardMarkup()
        for i in results:
            btn = InlineKeyboardButton(i, callback_data=f'action_{i}')
            markup.add(btn)

        bot.send_message(message.chat.id, 'Выбери фильм для дальнейших действий 🤗', reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так 🤗\n{str(e)}')


files_to_update = {}  # Словарь для хранения названий файлов, требующих обновления

# Обработчик выбора фильма для поиска по кнопке
@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def handle_file_actions(call: CallbackQuery):
    selected_file = call.data.split('_')[1:]
    selected_file = '_'.join(selected_file)

    files_to_update[selected_file] = call.from_user.id
    json_data = get_data(selected_file)
    countries = [ country['name'] for country in json_data['countries'] ]
    genres = [ name['name'] for name in json_data['genres'] ]
    
    bot.send_photo(call.message.chat.id, photo=json_data['poster'], caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}")


# @bot.callback_query_handler(func=lambda call: any(action in call.data for action in actions))
# def execute_file_action(call: CallbackQuery):
#     action, selected_file = call.data.split('_')[0], call.data.split('_')[1:]
#     selected_file = '_'.join(selected_file)

#     files_to_update[selected_file] = call.from_user.id

#     # Логика для скачивания файла
#     if action == 'Download':
#         if call.from_user.id == files_to_update.get(selected_file):
#             try:
#                 with sq.connect('db/database.db') as con:
#                     cur = con.cursor()
#                     cur.execute(f"SELECT data, format FROM files WHERE user_id = {call.from_user.id} AND name = '{selected_file}'")
#                     file_data, data_format = cur.fetchone()

#                     bot.send_document(call.message.chat.id, file_data, visible_file_name=f'{selected_file}.{data_format}')
                        
#                     del files_to_update[selected_file]
#             except Exception as e:
#                 bot.send_message(call.message.chat.id, f'Что-то пошло не так 🤗\n{str(e)}')
#         else:
#             bot.send_message(call.message.chat.id, 'У вас нет разрешения на доступ к этому файлу! ❌')


'''
Обработчик текстового сообщения для поиска фильма
'''
@bot.message_handler(content_types='text')
def text_searching(message: Message):
    global lastMessage

    json_data = get_data(message.text)
    countries = [ country['name'] for country in json_data['countries'] ]
    genres = [ name['name'] for name in json_data['genres'] ]
    lastMessage = message.text

    bot.send_photo(message.chat.id, photo=json_data['poster'], caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}")


if __name__ == '__main__':
    bot.infinity_polling()
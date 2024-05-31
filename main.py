from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
import sqlite3 as sq
import telebot
from os import getenv
import requests
from urllib.parse import quote
import json

bot = telebot.TeleBot(getenv('BOT_TOKEN'))
lastMessage = None
first_api_headers = {
    "accept": "application/json",
    "X-API-KEY": getenv('API_TOKEN')
}

second_api_headers = {
    "accept": "application/json",
    "X-API-KEY": getenv('X_API_KEY')
}

''' Функция для получения данных о фильме по названию '''
def get_data(name):
    url = f"https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=1&query={quote(name)}"
    data = json.loads(requests.get(url, headers=first_api_headers).text)

    try:
        data = data['docs'][0]
        json_data = {
            'id': data['id'],
            'name': data['name'],
            'alternativeName': data['alternativeName'],
            'countries': data['countries'],
            'year': data['year'],
            'genres': data['genres'],
            'description': data['shortDescription'],
            'poster': data['poster']['previewUrl']
        }
        return json_data
    except Exception as e:
        return str(e)
    

''' Обработчик команды /start для регистрации нового пользователя '''
@bot.message_handler(commands=['start'])
def start(message: Message):
    with sq.connect('db/database.db') as con: 
        cur = con.cursor()
        cur.execute('INSERT INTO users (user_id, user_name, user_surname, username) VALUES (?, ?, ?, ?) ON CONFLICT (user_id) DO NOTHING',
                    (message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username))
        con.commit()
    bot.send_message( message.chat.id, 'Шмебьюлок 👋' )


''' Обработчик команды /help '''
@bot.message_handler(commands=['help'])
def start(message: Message):
    text = '🍄 Инструкция 🍄\n/start - регистрация нового пользователя\n/add [название] [год] - добавление фильма по названию и году\n/add - добавление последнего фильма из поиска\n/all - все добавленные вами фильмы\nА еще можно выполнить поиск сразу, без добавления его в список. Для этого просто введите его название.'
    bot.send_message( message.chat.id, text)


''' Обработчик команды /add [название] [дата] для добавления фильма по названию и дате (необязательна)
    или /add для добавления последнего фильма из поиска по тексту ф. text_searching() '''
@bot.message_handler(commands=['add'])
def add_item(message):  
    global lastMessage

    if len(message.text) <= 5:  # Выполнение поиска по названию, введенному для функции text_searching()
        try:
            json_data = get_data(lastMessage)
        except TypeError:
            bot.reply_to(message, 'Пожалуйста, введите название фильма.')
    elif len(message.text) >= 5:    # Поиск фильма по названию из команды /add [название] [год]
        name = message.text.split(' ', 1)[1]
        try:
            json_data = get_data(name)
        except IndexError:
            bot.reply_to(message, 'Пожалуйста, введите название фильма.')
        except Exception as e:
            bot.reply_to(message, f'При получении данных произошла ошибка. Пожалуйста, попробуйте снова позже. ❌\n\n{str(e)}')
    try:
        with sq.connect('db/database.db') as con:   # Добавление в базу
            cur = con.cursor()
            cur.execute("INSERT INTO items (ru_name, alternative_name, year, genres, id_user) VALUES (?, ?, ?, ?, ?) ON CONFLICT (ru_name) DO NOTHING", 
                        (json_data['name'], json_data['alternativeName'], json_data['year'], json.dumps(json_data['genres'], ensure_ascii=False), message.from_user.id))
            con.commit()
    except Exception as e:
        return
    bot.reply_to(message, f'Фильм успешно добавлен! 🎉')


old_message_id = None
''' Обработчик команды /all для вывода всех добавленных фильмов '''
@bot.message_handler(commands=['all'])
def get_movies_info(message: Message):
    global old_message_id
    old_message_id = message.message_id

    try:
        with sq.connect('db/database.db') as con: 
            cur = con.cursor()
            cur.execute(f'SELECT ru_name FROM items WHERE id_user = {message.from_user.id}')
            results = [res[0] for res in cur.fetchall()]
        if not results:
            bot.send_message(message.chat.id, 'У вас нет ни одного фильма 🤗')
            return
        markup = InlineKeyboardMarkup()     # Формирование клавиатуры
        for result in results:
            btn = InlineKeyboardButton(result, callback_data=f'action_{result}')
            markup.add(btn)

        bot.send_message(message.chat.id, 'Выбери фильм для дальнейших действий 🤗', reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так 🤗\n{str(e)}')


''' Обработчик выбора фильма для поиска по кнопке '''
@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def handle_movies_actions(call: CallbackQuery):
    global old_message_id
    selected_movie = call.data.split('_')[1:]
    selected_movie = '_'.join(selected_movie)

    json_data = get_data(selected_movie)
    countries = [ country['name'] for country in json_data['countries'] ]
    genres = [ name['name'] for name in json_data['genres'] ]

    lnk = f'смотреть%20{json_data["name"].replace(" ", "%20")}%20{json_data["year"]}%20онлайн'

    markup = InlineKeyboardMarkup()
    btn_google = InlineKeyboardButton(text='Google', url=f'https://www.google.com/search?q={lnk}')
    btn_yandex = InlineKeyboardButton(text='Яндекс', url=f'https://yandex.ru/search/?text={lnk}')
    btn_delete = InlineKeyboardButton(text='🍄 Шмебьюлок 🍄',  callback_data=f'delete_{selected_movie}')

    markup.add(btn_google, btn_yandex)
    markup.add(btn_delete)

    if call.message.message_id != old_message_id:   # Сравнение идентификаторов сообщений
        bot.send_photo(call.message.chat.id, photo=json_data['poster'],
                       caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}",
                       reply_markup=markup)
        old_message_id = call.message.message_id    # Обновление идентификатора
    else:
        bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id + 1,
                               media=InputMediaPhoto(json_data['poster'], 
                               caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}"), 
                               reply_markup=markup)
        

''' Обработчик удаления фильма по кнопке '''
@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_movies_delete(call: CallbackQuery):
    selected_movie = call.data.split('_')[1:]
    selected_movie = '_'.join(selected_movie)

    with sq.connect('db/database.db') as con:
        cur = con.cursor()
        cur.execute(f'DELETE FROM items WHERE ru_name = ? and id_user = ?', (selected_movie, call.from_user.id))
        con.commit()

    bot.send_message(call.message.chat.id, 'Произошел шмебьюлок, фильм был удален 🍄')


''' Обработчик поиска похожего фильма по id '''
@bot.message_handler(commands=['similar'])
def similar_by_id(message: Message):
    # Получение id
    name = message.text.split(' ', 1)[1]
    json_data = get_data(name)
    
    id = json_data['id']
    try:    # Поиск похожего фильма по id
        url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{id}/similars"
        data = json.loads(requests.get(url, headers=second_api_headers).text)
        print(data)
        data = data['items'][0]
        json_data = {
            'name': data['nameRu'],
            'alternativeName': data['nameEn'],
            'poster': data['posterUrlPreview']
        }
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так 🤗\n{str(e)}')

    markup = InlineKeyboardMarkup()
    lnk = f'смотреть%20{json_data["name"].replace(" ", "%20")}%20онлайн'
    btn_google = InlineKeyboardButton(text='Google', url=f'https://www.google.com/search?q={lnk}')
    btn_yandex = InlineKeyboardButton(text='Яндекс', url=f'https://yandex.ru/search/?text={lnk}')
    markup.add(btn_google, btn_yandex)

    bot.send_photo(message.chat.id, photo=json_data['poster'], 
                   caption=f"{json_data['name']} ({json_data['alternativeName']})",
                   reply_markup=markup)


''' Обработчик текстового сообщения для поиска фильма '''
@bot.message_handler(content_types='text')
def text_searching(message: Message):
    global lastMessage

    json_data = get_data(message.text)
    countries = [ country['name'] for country in json_data['countries'] ]
    genres = [ name['name'] for name in json_data['genres'] ]
    lastMessage = message.text

    markup = InlineKeyboardMarkup()
    lnk = f'смотреть%20{json_data["name"].replace(" ", "%20")}%20{json_data["year"]}%20онлайн'
    btn_google = InlineKeyboardButton(text='Google', url=f'https://www.google.com/search?q={lnk}')
    btn_yandex = InlineKeyboardButton(text='Яндекс', url=f'https://yandex.ru/search/?text={lnk}')
    btn_add = InlineKeyboardButton(text='Добавить', callback_data=f'add_{json_data["id"]}')
    markup.add(btn_google, btn_yandex)
    markup.add(btn_add)

    bot.send_photo(message.chat.id, photo=json_data['poster'], 
                   caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}",
                   reply_markup=markup)


''' Обработчик добавления фильма по кнопке '''
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def handle_movies_delete(call: CallbackQuery):
    json_data = get_data(lastMessage)
    try:
        with sq.connect('db/database.db') as con:   # Добавление в базу
            cur = con.cursor()
            cur.execute(f"INSERT INTO items (ru_name, alternative_name, year, genres, id_user) VALUES (?, ?, ?, ?, ?)", 
                        (json_data['name'], json_data['alternativeName'], json_data['year'], json.dumps(json_data['genres'], ensure_ascii=False), call.from_user.id))
            con.commit()
    except Exception as e:
        return
    bot.send_message(call.message.chat.id, f'Фильм успешно добавлен! 🎉')


if __name__ == '__main__':
    bot.infinity_polling()
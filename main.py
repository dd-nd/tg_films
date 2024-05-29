from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import sqlite3 as sq
import telebot
from os import getenv
import requests
from urllib.parse import quote
import json

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
            'description': data['shortDescription'],
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
Обработчик команды /add [название] [дата] для добавления фильма по названию и дате (необязательна)
или /add для добавления последнего фильма из поиска по тексту ф. text_searching()
'''
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

    with sq.connect('db/database.db') as con:   # Добавление в базу
        cur = con.cursor()
        cur.execute("INSERT INTO items (ru_name, alternative_name, year, genres, id_user) VALUES (?, ?, ?, ?, ?) ON CONFLICT (ru_name) DO NOTHING", 
                    (json_data['name'], json_data['alternativeName'], json_data['year'], json.dumps(json_data['genres'], ensure_ascii=False), message.from_user.id))
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
        markup = InlineKeyboardMarkup()     # Формирование клавиатуры
        for i in results:
            btn = InlineKeyboardButton(i, callback_data=f'action_{i}')
            markup.add(btn)

        bot.send_message(message.chat.id, 'Выбери фильм для дальнейших действий 🤗', reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так 🤗\n{str(e)}')



'''
Обработчик выбора фильма для поиска по кнопке
'''
@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def handle_file_actions(call: CallbackQuery):
    selected_movie = call.data.split('_')[1:]
    selected_movie = '_'.join(selected_movie)

    json_data = get_data(selected_movie)
    countries = [ country['name'] for country in json_data['countries'] ]
    genres = [ name['name'] for name in json_data['genres'] ]
    
    markup = InlineKeyboardMarkup()
    lnk = f'смотреть%20{json_data["name"].replace(" ", "%20")}%20{json_data["year"]}%20онлайн'
    btn_google = InlineKeyboardButton(text='Google', url=f'https://www.google.com/search?q={lnk}')
    btn_yandex = InlineKeyboardButton(text='Яндекс', url=f'https://yandex.ru/search/?text={lnk}')
    markup.add(btn_google, btn_yandex)

    bot.send_photo(call.message.chat.id, photo=json_data['poster'], 
                   caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}", 
                   reply_markup=markup)


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

    markup = InlineKeyboardMarkup()
    lnk = f'смотреть%20{json_data["name"].replace(" ", "%20")}%20{json_data["year"]}%20онлайн'
    btn_google = InlineKeyboardButton(text='Google', url=f'https://www.google.com/search?q={lnk}')
    btn_yandex = InlineKeyboardButton(text='Яндекс', url=f'https://yandex.ru/search/?text={lnk}')
    markup.add(btn_google, btn_yandex)

    bot.send_photo(message.chat.id, photo=json_data['poster'], 
                   caption=f"{json_data['name']} ({json_data['alternativeName']})\n\n{', '.join(countries)}, {json_data['year']}\n\n{', '.join(genres)}\n\n{json_data['description']}",
                   reply_markup=markup)


if __name__ == '__main__':
    bot.infinity_polling()
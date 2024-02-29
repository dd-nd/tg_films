import sqlite3

with sqlite3.connect('content.db') as con:
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS genres(
    id_gen INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    id_cat INTEGER NOT NULL,
    FOREIGN KEY (id_cat) REFERENCES categories(id_cat)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS categories(
    id_cat INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS items(
    id_con INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    id_cat INTEGER NOT NULL,
    id_gen INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    FOREIGN KEY (id_cat) REFERENCES categories(id_cat),
    FOREIGN KEY (id_gen) REFERENCES genres(id_gen),
    FOREIGN KEY (id_user) REFERENCES users(user_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id name INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    user_surname TEXT,
    username STRING
    )''')
print('БД создана')
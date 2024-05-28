import sqlite3 as sq

with sq.connect('db/database.db') as con:
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY NOT NULL,
                user_name varchar,
                user_surname varchar,
                username varchar)''')
    
    # cur.execute('''CREATE TABLE IF NOT EXISTS genres(
    #             id INTEGER PRIMARY KEY AUTOINCREMENT, 
    #             name varchar)''')
    
    # cur.execute('''CREATE TABLE IF NOT EXISTS types(
    #             id INTEGER PRIMARY KEY AUTOINCREMENT, 
    #             name varchar)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS statuses(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name varchar)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                ru_name varchar UNIQUE, 
                alternative_name varchar,
                genres varchar,
                id_status INTEGER,
                id_user INTEGER, 
                FOREIGN KEY (id_status) references statuses(id),
                FOREIGN KEY (id_user) references users(id))''')

    # cur.execute('''INSERT INTO genres (name) VALUES ('Боевик'), ('Комедия'), ('Драма'), 
    #                                                 ('Мелодрама'), ('Триллер'), ('Научная фантастика'), 
    #                                                 ('Фэнтези'), ('Ужасы'), ('Приключения'), ('Другое')''')
    # cur.execute('''INSERT INTO types (name) VALUES ('Фильм'), ('Мультфильм'), ('Аниме')''')
    cur.execute('''INSERT INTO statuses (name) VALUES ('Планирую'), ('В процессе'), ('Смотрел')''')

    con.commit()
    print('БД создана')
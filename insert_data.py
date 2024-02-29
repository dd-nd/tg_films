import sqlite3

genres = [
    ('Боевик', 1),
    ('Детектив', 1),
    ('Мистика', 1),
    ('Ужасы', 1),
    ('Мелодрама', 1),
    ('Фантастика', 1),
    ('Фильм-катастрофа', 1),
    ('Комедия', 1),
    ('Аниме', 1),
    ('Боевик', 4),
    ('Детектив', 4),
    ('Мистика', 4),
    ('Ужасы', 4),
    ('Мелодрама', 4),
    ('Фантастика', 4),
    ('Фильм-катастрофа', 4),
    ('Комедия', 4),
    ('Аниме', 4)
]

categs = [
    ('Фильм',),
    ('Книга',),
    ('Песня',),
    ('Сериал',)
]

with sqlite3.connect('content.db') as con:
    cur = con.cursor()   
    cur.executemany("INSERT INTO categories (name) VALUES (?)", categs)
    cur.executemany("INSERT INTO genres (name, id_cat) VALUES (?,?)", genres)

print("Данные были добавлены в таблицу")
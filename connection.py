import psycopg2

try:
    conn = psycopg2.connect(dbname='films_py', user='postgres', password='123', host='localhost')
except:
    print('Не удается подключиться к базе данных')
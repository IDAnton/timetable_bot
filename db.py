# -*- coding: utf8 -*-
import psycopg2
import datetime
import os
from dotenv import load_dotenv
from tutors_parser.tutor_parser import tutor_serializer

PRODUCTION = True


def ensure_connection(func):
    def inner(*args, **kwargs):
        load_dotenv(".env")
        if PRODUCTION:
            with psycopg2.connect(dbname=os.environ.get('POSTGRES_DB'),  host='db', user=os.environ.get('POSTGRES_USER'), password=os.environ.get('POSTGRES_PASSWORD'),  port='5432') as conn:
                kwargs['conn'] = conn
                res = func(*args, **kwargs)
        else:
            with psycopg2.connect(dbname='nsu',  host='localhost', user='postgres', password='_',  port='5432') as conn:
                kwargs['conn'] = conn
                res = func(*args, **kwargs)
        return res
    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id     INT,
            user_name   TEXT,
            group_id    TEXT,
            mode        TEXT,
            UNIQUE(user_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id        TEXT,
            group_content   TEXT,
            UNIQUE(group_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS notify (
            user_id        INT,
            user_name      TEXT,
            time           TEXT,
            UNIQUE(user_id)
        )
    ''')


@ensure_connection
def set_user(conn, user_id, user_name):
    c = conn.cursor()
    c.execute('INSERT INTO users (user_id, user_name) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET user_name = %s', (user_id, user_name, user_name))
    conn.commit()


@ensure_connection
def get_all_users_id(conn):
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    res = c.fetchall()
    return res



@ensure_connection
def set_group_for_user(conn, user_id, group_id):
    c = conn.cursor()
    c.execute('UPDATE users SET group_id = %s WHERE user_id = %s', (group_id, user_id))
    conn.commit()


@ensure_connection
def get_group(conn, user_id):
    c = conn.cursor()
    c.execute('SELECT group_id FROM users WHERE user_id = %s', (user_id,))
    res = c.fetchone()[0]
    return res


@ensure_connection
def get_group_all(conn):
    c = conn.cursor()
    c.execute('SELECT group_id FROM groups')
    res = c.fetchall()
    return res


@ensure_connection
def set_group(conn, group_id, group_content):
    c = conn.cursor()
    c.execute('INSERT INTO groups (group_id, group_content) VALUES (%s, %s) ON CONFLICT (group_id) DO UPDATE SET group_content = %s', (group_id, group_content, group_content))
    conn.commit()


@ensure_connection
def get_group_content(conn, group_id):
    c = conn.cursor()
    c.execute('SELECT group_content FROM groups WHERE group_id = %s', (group_id,))
    res = c.fetchone()
    if res is None:
        return None
    return res[0]


@ensure_connection
def set_user_notify(conn, user_id, user_name, time):
    c = conn.cursor()
    c.execute('INSERT INTO notify (user_id, user_name, time) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET user_name = %s, time = %s', (user_id, user_name, time, user_name, time))
    conn.commit()


@ensure_connection
def set_user_weather_notify(conn, user_id, user_name, time):
    c = conn.cursor()
    c.execute('INSERT INTO notify (user_id, user_name, weather) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET user_name = %s, weather = %s', (user_id, user_name, time, user_name, time))
    conn.commit()


@ensure_connection
def get_users_to_notify(conn):
    c = conn.cursor()
    c.execute('SELECT user_id, time, weather, user_name from notify')
    res = c.fetchall()
    return res


@ensure_connection
def get_users_to_notify_weather(conn):  # TODO: delete this function
    c = conn.cursor()
    c.execute('SELECT user_id, weather from notify')
    res = c.fetchall()
    return res


@ensure_connection
def check_sub_user(conn, user_id):
    c = conn.cursor()
    c.execute('SELECT time FROM notify WHERE user_id = %s', (user_id,))
    res = c.fetchone()
    if res is None:
        return False
    if res[0] is not None:
        return True
    return False


@ensure_connection
def check_sub_user_weather(conn, user_id):
    c = conn.cursor()
    c.execute('SELECT weather FROM notify WHERE user_id = %s', (user_id,))
    res = c.fetchone()
    if res is None:
        return False
    if res[0] is not None:
        return True
    return False


@ensure_connection
def add_custom(conn, user_id, content):
    pass


@ensure_connection
def add_to_stats(conn):
    now = datetime.datetime.now() + datetime.timedelta(hours=0)
    day = str(datetime.datetime.combine(now.date(), datetime.time()))
    c = conn.cursor()
    c.execute('SELECT requests FROM stats WHERE day = %s', (day,))
    res = c.fetchall()
    if not res:
        c.execute('INSERT into stats (day, requests) VALUES (%s, %s)', (day, 1))
        conn.commit()
        return

    req = int(res[0][0]) + 1
    c.execute('INSERT into stats (day, requests) VALUES (%s, %s)  ON CONFLICT (day) DO UPDATE SET requests = %s', (day, req, req))
    conn.commit()


@ensure_connection
def get_stats(conn):
    c = conn.cursor()
    c.execute('select requests from stats order by day desc;')
    all = [day[0] for day in c.fetchall()]
    res = all[0:7]
    return res


@ensure_connection
def set_weather(conn, temp, main=None):
    c = conn.cursor()
    c.execute('UPDATE weather SET temp = %s WHERE id = %s', (temp, 1))
    c.execute('UPDATE weather SET main = %s WHERE id = %s', (main, 1))
    conn.commit()


@ensure_connection
def set_forecast_weather(conn, forecast):
    c = conn.cursor()
    c.execute('UPDATE weather SET forecast = %s WHERE id = %s', (forecast, 1))
    conn.commit()


@ensure_connection
def get_weather(conn):
    c = conn.cursor()
    c.execute('select temp from weather where id = 1;')
    res1 = c.fetchone()[0]
    c.execute('select main from weather where id = 1;')
    res2 = c.fetchone()[0]
    return [res1, res2]


@ensure_connection
def get_forecast_weather(conn):
    c = conn.cursor()
    c.execute('select forecast from weather where id = 1;')
    res1 = c.fetchone()[0]
    return res1


@ensure_connection
def initialize_tutors(conn):
    tutors = tutor_serializer()
    c = conn.cursor()
    id = 1
    for tutor in tutors:
        c.execute('INSERT into tutors (id, name, surname, patronymic, stat) values (%s, %s, %s, %s, %s)',
                  (id, tutor['name'], tutor['surname'], tutor['patronymic'], 0))
        conn.commit()
        id += 1


@ensure_connection
def get_tutors_by_surname(conn, surname):
    c = conn.cursor()
    c.execute('select * from tutors where surname = %s order by stat', (surname, ))
    tutors = c.fetchall()
    res = []
    for tutor in tutors:
        res.append({'name': tutor[0], 'surname': tutor[1], 'patronymic': tutor[2], 'stats': tutor[3], 'id': tutor[4]})
    return res


@ensure_connection
def check_reviewed(conn, user_id, tutor_id):
    c = conn.cursor()
    c.execute('select id, text from reviews where user_id = %s and tutor_id = %s', (user_id, tutor_id))
    res = c.fetchone()
    if res is None:
        return 'Rating'
    if res[1] is None:
        return 'Text'
    return 'Exists'


@ensure_connection
def add_review_rating(conn, user_id, tutor_id, rating, date):
    c = conn.cursor()
    c.execute('insert into reviews(user_id, rating, tutor_id, likes, dislikes, date) values (%s, %s, %s, 0, 0, %s)', (user_id, rating, tutor_id, date))
    c.execute('update tutors set stat = stat + 1 where id = %s', (tutor_id,))
    conn.commit()


@ensure_connection
def add_review_text(conn, user_id, tutor_id, text):
    c = conn.cursor()
    c.execute('update reviews set text = %s where user_id = %s and tutor_id = %s', (text, user_id, tutor_id))
    conn.commit()

@ensure_connection
def get_review(conn, tutor_id):
    c = conn.cursor()
    c.execute('select * from reviews where tutor_id = %s order by date DESC', (tutor_id,))
    res = c.fetchall()
    return res


@ensure_connection
def get_review_by_id(conn, review_id):
    c = conn.cursor()
    c.execute('select * from reviews where id = %s', (review_id,))
    res = c.fetchone()
    return res


@ensure_connection
def get_tutor_info(conn, tutor_id):
    c = conn.cursor()
    c.execute('select rating from reviews where tutor_id = %s', (tutor_id,))
    reviews = c.fetchall()
    review_len = len(reviews)
    sum_ratings = 0
    for review in reviews:
        sum_ratings += review[0]
    if review_len > 0:
        rating = sum_ratings / review_len
    else:
        rating = 0
    c.execute('select surname, name, patronymic from tutors where id = %s', (tutor_id,))
    tutor_name = c.fetchone()
    return {'rating': rating, 'amount': review_len, 'name': tutor_name}


@ensure_connection
def set_review_like(conn, user_id, review_id, like_type):
    c = conn.cursor()
    if like_type:
        c.execute('update reviews set likes = likes + 1 where id = %s ', (review_id,))
        c.execute('insert into review_likes(like_type, review_id, user_id) values(%s, %s, %s)', ('like', review_id, user_id))
    else:
        c.execute('update reviews set dislikes = dislikes + 1 where id = %s ', (review_id,))
        c.execute('insert into review_likes(like_type, review_id, user_id) values(%s, %s, %s)', ('dislike', review_id, user_id))
    conn.commit()


@ensure_connection
def check_if_liked(conn, user_id, review_id):
    c = conn.cursor()
    c.execute('select like_type from review_likes where user_id = %s and review_id = %s', (user_id, review_id))
    res = c.fetchone()
    if res is None:
        return False
    return res[0]


@ensure_connection
def get_review_like_count(conn, review_id):
    c = conn.cursor()
    c.execute('select like_type from review_likes where review_id = %s', (review_id,))
    likes = c.fetchall()
    res = {'likes': 0, 'dislikes': 0}
    if likes is not None:
        for like in likes:
            if like[0] == 'like':
                res['likes'] += 1
            if like[0] == 'dislike':
                res['dislikes'] += 1
    return res


@ensure_connection
def set_custom_timetable(conn, user_id, timetable, group_id):
    c = conn.cursor()
    c.execute('insert into custom_timetable(user_id, timetable, group_id) values(%s, %s, %s)'
              'on conflict (user_id, group_id) do update '
              'set timetable = %s', (user_id, timetable, group_id, timetable))
    conn.commit()


@ensure_connection
def get_custom_timetable(conn, user_id, group_id):
    c = conn.cursor()
    c.execute('select timetable from custom_timetable where user_id = %s and group_id = %s', (user_id, group_id))
    timetable = c.fetchone()
    return timetable[0] if timetable is not None else None


@ensure_connection
def get_custom_timetable_by_group(conn, group_id):
    c = conn.cursor()
    c.execute('select timetable, user_id from custom_timetable where group_id = %s', (group_id,))
    timetable = [[i[0], i[1]] for i in c.fetchall()]
    return timetable


@ensure_connection
def check_if_custom_active(conn, user_id, group_id):
    c = conn.cursor()
    c.execute('select active from custom_timetable where user_id=%s and group_id=%s', (user_id, group_id,))
    res = c.fetchone()
    return res[0] if res is not None else False


@ensure_connection
def set_custom_active(conn, user_id, group_id, state):
    c = conn.cursor()
    c.execute('update custom_timetable set active = %s where user_id=%s and group_id=%s', (state, user_id, group_id))
    conn.commit()


@ensure_connection
def delete_custom(conn, user_id, group_id):
    c = conn.cursor()
    c.execute('delete from custom_timetable where user_id=%s and group_id=%s', (user_id, group_id))
    conn.commit()


if __name__ == '__main__':
    print(get_stats())


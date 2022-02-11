from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

import custom_timetable
import db
from weather import get_weather
from db import check_sub_user, get_tutor_info, get_review_like_count

import json
import misc

REVIEW_SYMBOL = '⭐'

DEFAULT_SUBJECT_EMOJ = '📚'
DEFAULT_TUTOR_EMOJ = '👨‍🏫'
DEFAULT_ROOM_EMOJ = '🚪'

def menu_names(notify_text=None, user_id=None):
    weather_txt = "Погода"
    try:
        weather_emoji = get_weather()[-1]
        weather_txt += ' ' + weather_emoji
    except Exception as e:
        print('weather_keyboard !!! :', repr(e))

    return ReplyKeyboardMarkup(([[KeyboardButton('Сегодня'), KeyboardButton('Завтра')],
                                 [KeyboardButton('Неделя'), KeyboardButton('Сменить группу')],
                                 [KeyboardButton('Редактировать'), KeyboardButton(weather_txt)]]), resize_keyboard=True)


def time_for_notify(user_input, buttons_type):
    hours, minutes = user_input.split(':')
    if len(minutes) == 1:
        minutes += '0'
    user_input = hours + ':' + minutes

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("- 1 час", callback_data=json.dumps({'content': '-60', 'type': buttons_type})),
          InlineKeyboardButton(user_input,
                               callback_data=json.dumps({'content': 'OK' + user_input, 'type': buttons_type})),
          InlineKeyboardButton("+ 1 час", callback_data=json.dumps({'content': '+60', 'type': buttons_type}))],
         [InlineKeyboardButton("- 15 минут", callback_data=json.dumps({'content': '-15', 'type': buttons_type})),
          InlineKeyboardButton("+ 15 минут", callback_data=json.dumps({'content': '+15', 'type': buttons_type}))]]
        )
    return keyboard


def review_search_list(tutors):
    buttons = []
    for tutor in tutors:
        buttons.append(
            [
                InlineKeyboardButton(
                    str(tutor['surname']) + ' ' + str(tutor['name']) + ' ' + str(tutor['patronymic']),
                    callback_data=json.dumps({'content': tutor['id'], 'type': 'search'})
                )
            ]
        )
    keyboard = InlineKeyboardMarkup(buttons)
    return keyboard


def reviews_menu(input_mode='review_search'):
    if input_mode == 'review_search':
        return ReplyKeyboardMarkup([[KeyboardButton('Назад ⬅')]], resize_keyboard=True)
    if input_mode == 'review_done':
        return ReplyKeyboardMarkup(([[KeyboardButton('Анонимно написать отзыв')], [KeyboardButton('Посмотреть отзывы')],
                                    [KeyboardButton('Назад ⬅')]]), resize_keyboard=True)


def review_rating_keyboard():
    symbol = REVIEW_SYMBOL
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(symbol*5, callback_data=json.dumps({'content': 5, 'type': 'rating'}))],
        [InlineKeyboardButton(symbol*4, callback_data=json.dumps({'content': 4, 'type': 'rating'}))],
        [InlineKeyboardButton(symbol*3, callback_data=json.dumps({'content': 3, 'type': 'rating'}))],
        [InlineKeyboardButton(symbol*2, callback_data=json.dumps({'content': 2, 'type': 'rating'}))],
        [InlineKeyboardButton(symbol*1, callback_data=json.dumps({'content': 1, 'type': 'rating'}))]
    ])


def like_dislike_review(review_id):
    like_symbol = '👍'
    dislike_symbol = '👎'
    likes_dict = get_review_like_count(review_id=review_id)
    likes = likes_dict['likes']
    dislikes = likes_dict['dislikes']
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f'{like_symbol} {likes}', callback_data=json.dumps({'c': [review_id, 'l'], 'type': 'lk'})),
        InlineKeyboardButton(f'{dislike_symbol} {dislikes}', callback_data=json.dumps({'c': [review_id, 'd'], 'type': 'lk'})),
    ]])


def day_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Понедельник', callback_data=json.dumps({'content': 0, 'type': 'day_select'})),
        InlineKeyboardButton('Вторник', callback_data=json.dumps({'content': 1, 'type': 'day_select'}))],
        [InlineKeyboardButton('Среда', callback_data=json.dumps({'content': 2, 'type': 'day_select'})),
        InlineKeyboardButton('Четверг', callback_data=json.dumps({'content': 3, 'type': 'day_select'}))],
        [InlineKeyboardButton('Пятница', callback_data=json.dumps({'content': 4, 'type': 'day_select'})),
        InlineKeyboardButton('Суббота', callback_data=json.dumps({'content': 5, 'type': 'day_select'}))],
        [InlineKeyboardButton('🔧 Настройки', callback_data=json.dumps({'content': 10, 'type': 'day_select'})),
        InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 11, 'type': 'day_select'}))]
    ])


def custom_settings_keyboard(is_active):
    text = '🔄 '
    text += 'Переключить на обычное' if is_active else 'Переключить на кастомное'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=json.dumps({'content': 0, 'type': 'settings'}))],
        [InlineKeyboardButton('❌ Удалить', callback_data=json.dumps({'content': 1, 'type': 'settings'}))],
        [InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 7, 'type': 'time_select'}))]
    ])


def delete_custom_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('❌ Удалить', callback_data=json.dumps({'content': 2, 'type': 'settings'}))],
        [InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 10, 'type': 'day_select'}))]
    ])


def time_selection_keyboard(insert_content, user_id, group_id):
    origin = custom_timetable.get_origin(user_id, group_id)
    insert_content['time'] = 0
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        first = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        first = '1 пара (9:00 - 10:35)'
    insert_content['time'] = 1
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        second = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        second = '2 пара (10:50 - 12:25)'
    insert_content['time'] = 2
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        third = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        third = '3 пара (12:40 - 14:15)'
    insert_content['time'] = 3
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        fourth = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        fourth = '4 пара (14:30 - 16:05)'
    insert_content['time'] = 4
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        fifth = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        fifth = '5 пара (16:20 - 17:55)'
    insert_content['time'] = 5
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        sixth = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        sixth = '6 пара (18:10 - 19:45)'
    insert_content['time'] = 6
    if custom_timetable.get_subject_name(origin=origin, insert_content=insert_content):
        seven = misc.process_lesson_str(text=custom_timetable.get_subject_name(origin=origin, insert_content=insert_content), text_type='subject')
    else:
        seven = '7 пара (20:00 - 21:35)'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(first, callback_data=json.dumps({'content': 0, 'type': 'time_select'}))],
        [InlineKeyboardButton(second, callback_data=json.dumps({'content': 1, 'type': 'time_select'}))],
        [InlineKeyboardButton(third, callback_data=json.dumps({'content': 2, 'type': 'time_select'}))],
        [InlineKeyboardButton(fourth, callback_data=json.dumps({'content': 3, 'type': 'time_select'}))],
        [InlineKeyboardButton(fifth, callback_data=json.dumps({'content': 4, 'type': 'time_select'}))],
        [InlineKeyboardButton(sixth, callback_data=json.dumps({'content': 5, 'type': 'time_select'}))],
        [InlineKeyboardButton(seven, callback_data=json.dumps({'content': 6, 'type': 'time_select'}))],
        [InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 7, 'type': 'time_select'}))]
    ])


def many_already_exists_keyboards(texts: list):
    res = [[InlineKeyboardButton(texts[i], callback_data=json.dumps({'content': i, 'type': 'exists_many'}))] for i in range(len(texts))]
    res.append([InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 3, 'type': 'editing'}))])
    return InlineKeyboardMarkup(res)


def already_exists_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✏ Редактировать', callback_data=json.dumps({'content': 0, 'type': 'exists'})),
        InlineKeyboardButton('❌ Удалить', callback_data=json.dumps({'content': 1, 'type': 'exists'}))],
        [InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 3, 'type': 'editing'}))],
    ])


def editing_data_format(data):
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    time = ['1 пара', '2 пара', '3 пара', '4 пара', '5 пара', '6 пара', '7 пара']
    if data['day'] is not None:
        day = days[data['day']]
    else:
        day = None
    if data['time'] is not None:
        time_n = time[data['time']]
    else:
        time_n = None
    return {'day': day, 'time': time_n, 'subject': data['subject'], 'tutor': data['tutor'], 'room': data['room']}


def editing_keyboard(data):
    done_symbol = ''
    if data['subject'] is not None:
        emoj = '' if misc.is_emoji(data['subject']) else DEFAULT_SUBJECT_EMOJ
        subj_text = emoj + data['subject']
    else:
        subj_text = 'Предмет'
    if data['tutor'] is not None and data['tutor']:
        emoj = '' if misc.is_emoji(data['tutor']) else DEFAULT_TUTOR_EMOJ
        tutor_text = emoj + data['tutor']
    else:
        tutor_text = 'Преподаватель'
    if data['room'] is not None and data['room']:
        emoj = '' if misc.is_emoji(data['room']) else DEFAULT_ROOM_EMOJ
        rom_text = emoj + data['room']
    else:
        rom_text = 'Аудитория'
    week_text = data['week'].strip() if data['week'] != '' and data['week'] is not None and data['week'] else 'Каждую неделю'
    result = [
        [InlineKeyboardButton(subj_text, callback_data=json.dumps({'content': 0, 'type': 'editing'}))],
        [InlineKeyboardButton(tutor_text, callback_data=json.dumps({'content': 1, 'type': 'editing'}))],
        [InlineKeyboardButton(rom_text, callback_data=json.dumps({'content': 2, 'type': 'editing'}))],
        [InlineKeyboardButton(week_text, callback_data=json.dumps({'content': 5, 'type': 'editing'}))],
        [InlineKeyboardButton('↩ Назад', callback_data=json.dumps({'content': 3, 'type': 'editing'}))]
    ]
    if data['subject'] is not None:
        result[3].append(InlineKeyboardButton('✅ Сохранить', callback_data=json.dumps({'content': 4, 'type': 'editing'})))
    return InlineKeyboardMarkup(result)


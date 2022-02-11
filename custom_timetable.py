import db
import json

import misc

days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']


def init(group):
    json_data = db.get_group_content(group_id=str(group))
    data = json.loads(json_data)


def insert_lesson(origin, insert_content):
    origin[days[insert_content['day']]][insert_content['time']]['subject'] = [insert_content['subject']]
    origin[days[insert_content['day']]][insert_content['time']]['tutor'] = [insert_content['tutor']] if insert_content['tutor'] is not None else []
    origin[days[insert_content['day']]][insert_content['time']]['room'] = [insert_content['room']] if insert_content['room'] is not None else []
    origin[days[insert_content['day']]][insert_content['time']]['type'] = []
    origin[days[insert_content['day']]][insert_content['time']]['week'] = [insert_content['week']] if insert_content['week'] is not None else []
    origin[days[insert_content['day']]][insert_content['time']]['custom'] = True
    return origin


def delete_lesson(origin, insert_content, order=0):
    origin[days[insert_content['day']]][insert_content['time']]['subject'].pop(order)
    if origin[days[insert_content['day']]][insert_content['time']]['tutor']:
        origin[days[insert_content['day']]][insert_content['time']]['tutor'].pop(order)
    if origin[days[insert_content['day']]][insert_content['time']]['room']:
        origin[days[insert_content['day']]][insert_content['time']]['room'].pop(order)
    if origin[days[insert_content['day']]][insert_content['time']]['type']:
        origin[days[insert_content['day']]][insert_content['time']]['type'].pop(order)
    if origin[days[insert_content['day']]][insert_content['time']]['week']:
        origin[days[insert_content['day']]][insert_content['time']]['week'].pop(order)
    origin[days[insert_content['day']]][insert_content['time']]['custom'] = True
    return origin


def check_lesson(origin, insert_content):
    subjects = origin[days[insert_content['day']]][insert_content['time']]['subject']
    return False if subjects == [''] or subjects == [] else len(subjects)


def get_subject_name(origin, insert_content, order=0):
    return misc.process_lesson_str(text=origin[days[insert_content['day']]][insert_content['time']]['subject'][order], text_type='subject') if origin[days[insert_content['day']]][insert_content['time']]['subject'] else False


def get_subject_names(origin, insert_content):
    return [misc.process_lesson_str(text, text_type='subject') for text in origin[days[insert_content['day']]][insert_content['time']]['subject']]


def get_tutor_name(origin, insert_content, order=0):
    return misc.process_lesson_str(text=origin[days[insert_content['day']]][insert_content['time']]['tutor'][order], text_type='tutor') if origin[days[insert_content['day']]][insert_content['time']]['tutor'] else False


def get_room_name(origin, insert_content, order=0):
    return misc.process_lesson_str(text=origin[days[insert_content['day']]][insert_content['time']]['room'][order], text_type='room') if origin[days[insert_content['day']]][insert_content['time']]['room'] else False


def get_week_name(origin, insert_content, order=0):
    return origin[days[insert_content['day']]][insert_content['time']]['week'][order] if origin[days[insert_content['day']]][insert_content['time']]['week'] else False


def get_weeks_name(origin, insert_content):
    return origin[days[insert_content['day']]][insert_content['time']]['week'] if origin[days[insert_content['day']]][insert_content['time']]['week'] else False


def get_type_name(origin, insert_content, order=0):
    return origin[days[insert_content['day']]][insert_content['time']]['type'][order] if origin[days[insert_content['day']]][insert_content['time']]['type'] else False


def get_types_name(origin, insert_content):
    return origin[days[insert_content['day']]][insert_content['time']]['type'] if origin[days[insert_content['day']]][insert_content['time']]['type'] else False


def get_origin(user_id, group_id):
    origin = db.get_custom_timetable(user_id=user_id, group_id=group_id)
    if origin is None:
        origin = db.get_group_content(group_id=group_id)
    return json.loads(origin)


def update_custom(default, group_id):
    customs = db.get_custom_timetable_by_group(group_id=group_id)
    for data in customs:
        custom = json.loads(data[0])
        user_id = data[1]
        for day in days:
            for i in range(7):
                if 'custom' not in custom[day][i]:
                    custom[day][i] = default[day][i]
        db.set_custom_timetable(user_id=user_id, timetable=json.dumps(custom, ensure_ascii=False), group_id=group_id)


def add_to_custom(user_id, content):
    json_time_table = db.get_custom(user_id)
    data = json.loads(json_time_table)
    day = content['day']
    data[day].update()


if __name__ == '__main__':
    update_custom(383582494, '20304')

import datetime
import json
import db
import weather
import misc

TIMEZONE = 0
day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']


def get_group_week(group, user_id):
    now = datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE)
    week_start = datetime.datetime(2020, 1, 6)
    delta = now - week_start
    type = delta.days // 7 + 1
    if_next_week = False
    if now.weekday() == 6:  # return next week if saturday
        res = 'Расписание на следующую неделю\n' + '=' * 25 + '\n'
        if_next_week = True
    elif type % 2 == 0:
        res = 'Сейчас идет четная неделя\n' + '=' * 25 + '\n'
    else:
        res = 'Сейчас идет нечетная неделя\n' + '=' * 25 + '\n'
    for day in range(6):
        today = get_group_day(group=group, day=day,user_id=user_id, if_next_week=if_next_week)
        if not today.rstrip('\n') in day_names:
            res += today + '=' * 25 + '\n\n'
    res = res[:-2:] + '\n@NSUlog'
    return res


def get_group_today(group, user_id):
    now = datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE)
    day = now.weekday()
    return get_group_day(group=group, day=day, user_id=user_id) + '@NSUlog'


def get_group_tomorrow(group, user_id):
    now = datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE) + datetime.timedelta(days=1)
    day = now.weekday()
    if datetime.datetime.now().weekday() == 6:  # return next week if saturday
        return get_group_day(group=group, day=day, if_next_week=True, user_id=user_id) + '@NSUlog'
    return get_group_day(group=group, day=day, user_id=user_id) + '@NSUlog'


def get_group_day(group, day, user_id, if_next_week=False):
    time_emoj = '🕙'  # 🕙
    subject_emoj = '📚'  # 📚
    tutor_emoj = '👨‍🏫' # 👨‍🏫
    class_emoj = '🚪' # 🚪

    now = datetime.datetime.now()
    week_start = datetime.datetime(2020, 1, 6)
    delta = now - week_start
    type = delta.days // 7 + 1
    # path = 'time_table_old_jsons/' + group + '.json'
    # file = open(path, 'r', encoding='utf-8')
    custom_tt = db.get_custom_timetable(group_id=str(group), user_id=user_id)
    show_custom = db.check_if_custom_active(group_id=str(group), user_id=user_id)
    if custom_tt is not None and show_custom:
        data = json.loads(custom_tt)
    else:
        json_data = db.get_group_content(group_id=str(group))
        data = json.loads(json_data)

    def more_lessons(time_table, lesson_counter):  # if it is more lesson in this day
        for i in range(lesson_counter, len(time_table)):
            if time_table[i]['subject'] or check_if_no_lesson_this_week(time_table[i]):
                return True
        return False

    def check_if_no_lesson_this_week(data_day_local):  # True if no lesson this week
        if len(data_day_local['week']) == 1:
            if ((type + int(if_next_week)) % 2 == 1 and data_day_local['week'][0] == ' Четная') or (
                    (type + int(if_next_week)) % 2 == 0 and data_day_local['week'][0] == ' Нечетная'):
                return True
        return False

    if day == 6:
        return 'Отдыхай студент!\n'

    day_number = day
    day = day_names[day]

    res = day + '\n\n'
    data_day_all = data[day]
    time = [f'{time_emoj} 9:00 - 10:35', f'{time_emoj} 10:50 - 12:25', f'{time_emoj} 12:40 - 14:15', f'{time_emoj} 14:30 - 16:05', f'{time_emoj} 16:20 - 17:55',
            f'{time_emoj} 18:10 - 19:45', f'{time_emoj} 20:00 - 21:35']
    time_counter = 0
    make_windows = False
    for data_day in data_day_all:
        week_type = 0
        if len(data_day['week']) == 2:
            if (type + int(if_next_week)) % 2 == 0:
                week_type = 1
            if (type + int(if_next_week)) % 2 == 1:
                week_type = 0
        if data_day['subject'] and (not check_if_no_lesson_this_week(data_day)):
            make_windows = True
            if len(data_day['subject']) >= 2 and len(data_day['week']) == 0:  # 2 lessons in 1
                res += time[time_counter] + '\n'
                lesson_type = str(data_day['type'][0]) if data_day['type'] else ''
                res += subject_emoj + data_day['subject'][0] + ' ' + lesson_type + ' | ' + data_day['subject'][
                    1] + ' ' + data_day['type'][1] + '\n'
                if data_day['tutor']:
                    res += tutor_emoj + data_day['tutor'][0] + ' | ' + data_day['tutor'][1] + '\n'
                if data_day['room']:
                    res += class_emoj + data_day['room'][0] + ' | ' + data_day['room'][1] + '\n '
                res += '\n'
            else:  # default lesson
                res += time[time_counter] + '\n'
                lesson_type = str(data_day['type'][week_type]) if data_day['type'] else ''
                res += misc.process_lesson_str(data_day['subject'][week_type], text_type='subject') + ' ' + lesson_type + '\n'
                if data_day['tutor'] and data_day['tutor'] != ['']:
                    res += misc.process_lesson_str(data_day['tutor'][week_type], text_type='tutor') + '\n'
                if data_day['room'] and data_day['room'] != ['']:
                    res += misc.process_lesson_str(data_day['room'][week_type], text_type='room') + '\n '
                    if data_day['room'][week_type] == 'Ауд. Спортивный комплекс':  # Weather forecast for PE lesson
                        pe_weather = weather.forecast_for_pe(time[time_counter], day_number)
                        if pe_weather is not None:
                            res += '🌡 ' + pe_weather + '\n'
                res += '\n'
        if more_lessons(time_table=data_day_all, lesson_counter=time_counter) and not data_day['subject'] and make_windows:
            res += time[time_counter] + '\n'
            res += '\n' * 4
        time_counter += 1
    return res

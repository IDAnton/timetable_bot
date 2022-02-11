import re
from emoji import UNICODE_EMOJI
import custom_timetable
import keyboards


def is_emoji(text: str):
    text.replace(' ', '')
    return text[0] if text[0] in UNICODE_EMOJI['en'] else False


def format_text(text: str):
    res = re.sub(" +", " ", text)
    if is_emoji(text):
        if res[1] == ' ':
            return res[0] + res[2::]
    return res


def process_lesson_str(text, text_type):
    time_emoj = '🕙'  # 🕙
    subject_emoj = '📚'  # 📚
    tutor_emoj = '👨‍🏫'  # 👨‍🏫
    class_emoj = '🚪'  # 🚪
    if not text:
        return ''
    if is_emoji(text):
        return text
    else:
        if text_type == 'subject':
            return subject_emoj + text
        if text_type == 'tutor':
            return tutor_emoj + text
        if text_type == 'room':
            return class_emoj + text


def get_all_subjects_on_day(origin, insert_content, order=None) -> str:
    subjects = custom_timetable.get_subject_names(origin=origin, insert_content=insert_content)
    types = custom_timetable.get_types_name(origin=origin, insert_content=insert_content)
    weeks = custom_timetable.get_weeks_name(origin=origin, insert_content=insert_content)
    subject_text = ''
    if order is None:
        for i in range(len(subjects)):
            res_types = types[i] if types else ''
            res_weeks = weeks[i] if weeks else ''
            subject_text += f"{subjects[i]} {res_types}{res_weeks}\n"
    else:
        subject_text = f"{subjects[order]} {types[order]}{weeks[order]}\n"
    return subject_text


def get_all_subjects_on_day_list(origin, insert_content) -> list:
    subjects = custom_timetable.get_subject_names(origin=origin, insert_content=insert_content)
    types = custom_timetable.get_types_name(origin=origin, insert_content=insert_content)
    weeks = custom_timetable.get_weeks_name(origin=origin, insert_content=insert_content)
    subject_list = []
    for i in range(len(subjects)):
        subject_list.append(f"{subjects[i]} {types[i]}{weeks[i]}")
    return subject_list


def editing_text(context):
    return '🕙 ' + keyboards.editing_data_format(context.chat_data['edit_timetable'])['day'] + \
                   ', ' + keyboards.editing_data_format(context.chat_data['edit_timetable'])['time']\
                   + '\n\nНажми на кнопку и ' \
                     'заполни предмет, ' \
                     'препода и аудиторию. (' \
                     'Можно добавить только ' \
                     'название предмета, ' \
                     'остальное необязательно)'


def toggle_week(data):
    if data == "" or data is None or not data:
        return " Четная"
    if data == " Четная":
        return " Нечетная"
    if data == " Нечетная":
        return ""


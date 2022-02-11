# -*- coding: utf8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler, \
    ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, User, Audio, InlineKeyboardMarkup, \
    InlineKeyboardButton, ParseMode, Bot, Poll, ParseMode, ParseMode, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from telegram.ext.dispatcher import run_async
from uuid import uuid4
from dotenv import load_dotenv
import logging
import os
import db
import time
import group_updater as parser
import datetime
import timetable
import keyboards
import custom_timetable
import weather
import json
import reviews
import misc


db.init_db()

my_id = _

groups_tmp = db.get_group_all()
groups_lst = []
for group in groups_tmp:
    groups_lst.append(str(group[0]))
print(len(groups_lst), 'groups init')

logging.basicConfig(filename='log.txt',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)


def ensure_user_db(func):
    def inner(update, context):
        user_id = update.message.chat.id
        user_name = update.message.chat.username
        db.set_user(user_id=user_id, user_name=user_name)
        res = func(update, context)

    return inner


def ensure_fresh_msg(func):
    def inner(update, context):
        if int(update.message.date.timestamp()) < start_time:
            chat_id = update.message.chat.id
            logger.log('skipped update from {}'.format(str(chat_id)))
            return
        func(update, context)

    return inner


def add_custom(context, update):
    user_id = update.message.chat.id
    group = db.get_group(user_id=user_id)
    custom_timetable.init(group)


def set_weather_notify(update, context):
    if not db.check_sub_user_weather(user_id=update.message.chat.id):
        text = 'Выбери время, в которое присылать погоду:\n'
        if 'weather_update_time' not in context.chat_data:
            context.chat_data['weather_update_time'] = '8:00'
        time_str = context.chat_data['weather_update_time']
        context.bot.send_message(chat_id=update.message.chat.id, text=text,
                                 reply_markup=keyboards.time_for_notify(user_input=time_str, buttons_type='weather'))
    else:
        unset_weather_notify(update, context)


def unset_weather_notify(update, context):
    text = 'Больше не буду отправлять тебе прогноз погоды\n'
    user_id = update.message.chat.id
    db.set_user_weather_notify(user_id=user_id, user_name=update.message.from_user.username, time=None)
    context.bot.send_message(chat_id=user_id, text=text)


def sub_to_notify(update, context):
    if not db.check_sub_user(user_id=update.message.chat.id):
        text = 'Выбери время, в которое присылать расписание:\n' \
               '(Установи кнопками нужное время и НАЖМИ на него)'
        if 'notify_timetable_time' not in context.chat_data:
            context.chat_data['notify_timetable_time'] = '20:00'
        time_str = context.chat_data['notify_timetable_time']
        context.bot.send_message(chat_id=update.message.chat.id, text=text,
                                 reply_markup=keyboards.time_for_notify(user_input=time_str, buttons_type='timetable'))
    else:
        unsub_to_notify(update, context)


def unsub_to_notify(update, context):
    user_id = update.message.chat.id
    user_name = update.message.from_user.username
    db.set_user_notify(user_id=user_id, user_name=user_name, time=None)
    text = 'Больше не буду автоматически присылать расписание'
    context.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboards.menu_names(user_id=user_id))


def buttons(update, context):
    query = update.callback_query
    query.answer()
    loads = json.loads(update.callback_query.data)
    user_id = update.callback_query.message.chat.id
    if loads['type'] == 'weather':
        if 'weather_update_time' not in context.chat_data:
            context.chat_data['weather_update_time'] = '8:00'
        query = update.callback_query
        if json.loads(query.data)['content'][:2] == 'OK':
            set_time = json.loads(query.data)['content'].split('OK')[1]
            db.set_user_weather_notify(user_id=query.message.chat.id,
                                       user_name=query.message.chat.username, time=set_time)
            text = 'Жди весточку в ' + set_time + '\n'
            query.edit_message_text(text=text)
            return
        else:
            delta_minutes = int(json.loads(query.data)['content'])
            hours, minutes = map(int, context.chat_data['weather_update_time'].split(':'))
            set_time = datetime.datetime(2001, 9, 24, hours, minutes, 0)
            set_time = set_time + datetime.timedelta(minutes=delta_minutes)
            set_time = str(set_time.hour) + ':' + str(set_time.minute)
            context.chat_data['weather_update_time'] = set_time
            text = 'Выбери время, в которое присылать погоду:\n' \
                   '(Установи кнопками нужное время и НАЖМИ на него)\n'
            query.edit_message_text(text=text,
                                    reply_markup=keyboards.time_for_notify(user_input=set_time, buttons_type='weather'))
        return
    if loads['type'] == 'timetable':
        if 'notify_timetable_time' not in context.chat_data:
            context.chat_data['notify_timetable_time'] = '20:00'
        query = update.callback_query
        if json.loads(query.data)['content'][:2] == 'OK':
            set_time = json.loads(query.data)['content'].split('OK')[1]
            db.set_user_notify(user_id=update.callback_query.message.chat.id,
                               user_name=update.callback_query.message.chat.username, time=set_time)
            text = 'Жди весточку в ' + set_time + '\n'
            query.edit_message_text(text=text)
            return

        else:
            delta_minutes = int(json.loads(query.data)['content'])
            hours, minutes = map(int, context.chat_data['notify_timetable_time'].split(':'))
            set_time = datetime.datetime(2001, 9, 24, hours, minutes, 0)
            set_time = set_time + datetime.timedelta(minutes=delta_minutes)
            set_time = str(set_time.hour) + ':' + str(set_time.minute)
            context.chat_data['notify_timetable_time'] = set_time
            text = 'Выбери время, в которое присылать расписание:'
            query.edit_message_text(text=text, reply_markup=keyboards.time_for_notify(user_input=set_time,
                                                                                      buttons_type='timetable'))
    if loads['type'] == 'search':
        context.chat_data['tutor'] = loads['content']
        context.chat_data['input_mod'] = 'review_done'
        text = reviews.tutor_info(tutor_id=context.chat_data['tutor'])
        context.bot.send_message(chat_id=update.callback_query.message.chat.id, text=f'*{text}*',
                                 reply_markup=keyboards.reviews_menu(context.chat_data['input_mod']),
                                 parse_mode=ParseMode.MARKDOWN)
    if loads['type'] == 'rating':
        rating = loads['content']
        query = update.callback_query
        if not ('tutor' in context.chat_data):
            text = 'Произошел сбой. Попробуй еще раз'
            query.edit_message_text(text=keyboards.REVIEW_SYMBOL * rating)
            context.bot.send_message(chat_id=user_id, text=text,
                                     reply_markup=keyboards.menu_names(user_id=user_id))
        if reviews.add_review_rating(user_id=user_id, tutor_id=context.chat_data['tutor'], rating=rating):
            context.chat_data['input_mod'] = 'review_text'
            query.edit_message_text(text='⭐' * rating)
            text = '✅ Оценка добавлена\nТеперь можно дополнить ее текстовым отзывом\nИли выйти ⬅'
            context.bot.send_message(chat_id=user_id, text=text,
                                     reply_markup=keyboards.reviews_menu())
        else:
            text = 'Вы уже писали отзыв об этом преподавателе'
            context.bot.send_message(chat_id=user_id, text=text,
                                     reply_markup=keyboards.reviews_menu())
    if loads['type'] == 'lk':
        query = update.callback_query
        user_id = query.message.chat.id
        review_id, like_type = loads['c']
        text = reviews.like_review(user_id=user_id, review_id=review_id, like_type=like_type)
        try:
            query.edit_message_text(text=reviews.load_review_by_id(review_id=review_id),
                                    reply_markup=keyboards.like_dislike_review(review_id=review_id))
        except:
            pass
        context.bot.answer_callback_query(text=text, callback_query_id=query.id)

    if loads['type'] == 'day_select' and loads['content'] == 10:  # Settings menu
        group_id = db.get_group(user_id=user_id)
        is_active = db.check_if_custom_active(user_id=user_id, group_id=group_id)
        text = "Сейчас отображается:\n\nкастомное расписание" if is_active else "Сейчас отображается:\n\nобычное расписание как на сайте"
        query.edit_message_text(text=text, reply_markup=keyboards.custom_settings_keyboard(is_active=is_active))
        return

    if loads['type'] == 'day_select' and loads['content'] == 11:  # Exit from custom menu
        query.delete_message()
        context.bot.send_message(chat_id=user_id, text='⬅', reply_markup=keyboards.menu_names())
        return

    if loads['type'] == 'settings':
        group_id = db.get_group(user_id=user_id)
        if loads['content'] == 0:
            is_active = not db.check_if_custom_active(user_id=user_id, group_id=group_id)
            db.set_custom_active(user_id=user_id, group_id=group_id, state=is_active)
            text = "Сейчас отображается:\n\nкастомное расписание" if is_active else "Сейчас отображается:\n\nобычное расписание как на сайте"
            query.edit_message_text(text=text, reply_markup=keyboards.custom_settings_keyboard(is_active=is_active))

        if loads['content'] == 1:
            text = "Уверены что хотите удалить свое кастомное расписание ?"
            query.edit_message_text(text=text, reply_markup=keyboards.delete_custom_keyboard())

        if loads['content'] == 2:
            text = "❌ Кастомное расписание удалено."
            db.delete_custom(user_id=user_id, group_id=group_id)
            query.delete_message()
            context.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboards.menu_names())
        return

    if loads['type'] == 'day_select' or (loads['type'] == 'editing' and loads['content'] == 3):
        group_id = db.get_group(user_id=user_id)
        day_selected = loads['content'] if not (loads['type'] == 'editing' and loads['content'] == 3) else context.chat_data['edit_timetable']['day']
        context.chat_data['edit_timetable'] = {'day': day_selected, 'time': None, 'subject': None, 'tutor': None,
                                               'room': None, 'week': None, 'order': None}
        text = keyboards.editing_data_format(context.chat_data['edit_timetable'])['day'] + '\n\nВыбери пару'
        query.edit_message_text(text=text, reply_markup=keyboards.time_selection_keyboard(user_id=user_id, group_id=group_id, insert_content=context.chat_data['edit_timetable']))
        return
    if loads['type'] == 'time_select' and loads['content'] == 7:
        context.chat_data['edit_timetable'] = {}
        query.edit_message_text(text='На какой день изменить расписание ?',
                                reply_markup=keyboards.day_selection_keyboard())
        return
    if loads['type'] == 'exists_many':
        context.chat_data['edit_timetable']['order'] = loads['content']
    if (loads['type'] == 'time_select') or (loads['type'] == 'exists' and loads['content'] == 0) or loads['type'] == 'exists_many':
        if not (loads['type'] == 'exists' and loads['content'] == 0 or loads['type'] == 'exists_many'):
            context.chat_data['edit_timetable']['time'] = loads['content']
        group_id = db.get_group(user_id=user_id)
        origin = custom_timetable.get_origin(user_id=user_id, group_id=group_id)
        if custom_timetable.check_lesson(origin=origin, insert_content=context.chat_data['edit_timetable']) and not (loads['type'] == 'exists' and loads['content'] == 0):
            subject_text = misc.get_all_subjects_on_day(origin=origin, insert_content=context.chat_data['edit_timetable'], order=context.chat_data['edit_timetable']['order'])
            if custom_timetable.check_lesson(origin=origin, insert_content=context.chat_data['edit_timetable']) == 1 or context.chat_data['edit_timetable']['order'] is not None:
                text = f"🕙 {keyboards.editing_data_format(context.chat_data['edit_timetable'])['day']}, {keyboards.editing_data_format(context.chat_data['edit_timetable'])['time']}\n\n{subject_text}"
                keyboard = keyboards.already_exists_keyboard()
            else:
                text = f"🕙 {keyboards.editing_data_format(context.chat_data['edit_timetable'])['day']}, {keyboards.editing_data_format(context.chat_data['edit_timetable'])['time']}\n\nВыбери пару:"
                keyboard = keyboards.many_already_exists_keyboards(misc.get_all_subjects_on_day_list(origin=origin, insert_content=context.chat_data['edit_timetable']))
            query.edit_message_text(text=text, reply_markup=keyboard)
            return
        else:
            if loads['type'] == 'exists' and loads['content'] == 0:
                order = context.chat_data['edit_timetable']['order']
                order = 0 if order is None else order
                context.chat_data['edit_timetable']['subject'] = custom_timetable.get_subject_name(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
                context.chat_data['edit_timetable']['tutor'] = custom_timetable.get_tutor_name(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
                context.chat_data['edit_timetable']['room'] = custom_timetable.get_room_name(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
                context.chat_data['edit_timetable']['week'] = custom_timetable.get_week_name(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
                context.chat_data['edit_timetable']['type'] = custom_timetable.get_type_name(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
            text = misc.editing_text(context)
            query.edit_message_text(text=text, reply_markup=keyboards.editing_keyboard(context.chat_data['edit_timetable']))
        return
    if loads['type'] == 'editing':
        if loads['content'] == 0:
            text = 'Введи название предмета'
            context.chat_data['input_mod'] = 'editing_1'
        if loads['content'] == 1:
            text = 'Введи имя преподавателя'
            context.chat_data['input_mod'] = 'editing_2'
        if loads['content'] == 2:
            text = 'Введи Аудиторию'
            context.chat_data['input_mod'] = 'editing_3'
        if loads['content'] == 4:
            group_id = db.get_group(user_id=user_id)
            new_timetable = json.dumps(custom_timetable.insert_lesson(origin=custom_timetable.get_origin(user_id=user_id, group_id=group_id), insert_content=context.chat_data['edit_timetable']), ensure_ascii=False)
            db.set_custom_timetable(group_id=group_id, user_id=user_id, timetable=new_timetable)
            query.edit_message_text(text='Изменения внесены ✅', reply_markup=keyboards.time_selection_keyboard(context.chat_data['edit_timetable'], user_id, group_id))
            return
        if loads['content'] == 5:
            text = misc.editing_text(context)
            context.chat_data['edit_timetable']['week'] = misc.toggle_week(context.chat_data['edit_timetable']['week'])
            query.edit_message_text(text=text, reply_markup=keyboards.editing_keyboard(context.chat_data['edit_timetable']))
            return
        query.edit_message_text(text=text)
    if loads['type'] == 'exists' and loads['content'] == 1:
        group_id = db.get_group(user_id=user_id)
        origin = custom_timetable.get_origin(user_id=user_id, group_id=group_id)
        order = context.chat_data['edit_timetable']['order']
        order = 0 if order is None else order
        new_tt = custom_timetable.delete_lesson(origin=origin, insert_content=context.chat_data['edit_timetable'], order=order)
        db.set_custom_timetable(user_id=user_id, group_id=group_id, timetable=json.dumps(new_tt, ensure_ascii=False))
        query.edit_message_text(text='Пара удалена ❌', reply_markup=keyboards.time_selection_keyboard(context.chat_data['edit_timetable'], user_id, group_id))
        return


def inlinequery(update, context):
    query = update.inline_query.query
    user_id = update.inline_query.from_user.id
    if query == "":
        return
    group_id = query
    if group_id in groups_lst:
        today = f"Расписание на сегодня для {group_id}\n" + timetable.get_group_today(group=group_id, user_id=user_id)
        tomorrow = f"Расписание на завтра для {group_id}\n" + timetable.get_group_tomorrow(group=group_id, user_id=user_id)
        week = f"Расписание на неделю для {group_id}\n" + timetable.get_group_week(group=group_id, user_id=user_id)
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Сегодня",
                input_message_content=InputTextMessageContent(today),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Завтра",
                input_message_content=InputTextMessageContent(tomorrow),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="На неделю",
                input_message_content=InputTextMessageContent(week),
            ),
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f'Группа "{query}" не найдена 😞',
                input_message_content=InputTextMessageContent('😞'),
            ),
        ]
    update.inline_query.answer(results)


def get_notify_first_check(period):
    minutes = (period - (
                (datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE)).time().minute % period)) % period
    return minutes * 60


def send_msg_to_all(context):
    ban_list = []
    #text = ''
    users = db.get_all_users_id()
    for user in users:
        user_id = user[0]
        if int(user_id) in ban_list:
            print('skip' + str(user_id))
            continue
        try:
            #context.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboards.menu_names(), parse_mode=ParseMode.MARKDOWN)
            print(user_id)
        except:
            context.bot.send_message(chat_id=my_id, text=str(user_id))
        time.sleep(1)
    context.bot.send_message(chat_id=my_id, text='done')


def send_notification(context):  # TODO: refactor send_notification and send_weather_notification functions
    now = datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE)
    users_to_notify = db.get_users_to_notify()  # [user_id, time, weather_time]
    users_counter = 0
    for user in users_to_notify:
        time.sleep(1)
        if user[1] == 'yes':  # delete
            continue
        if user[1] is not None and user[1] != 'yes':  # timetable notify
            hours, minutes = map(int, user[1].split(':'))
            notify_time = datetime.datetime.combine(now.date(), datetime.time(hours, minutes))
            if now > notify_time and (now - notify_time).seconds / 60 < 15:
                if now.hour < 14:
                    text = timetable.get_group_today(group=db.get_group(user_id=user[0]))
                else:
                    if now.weekday() == 5:
                        return
                    text = timetable.get_group_tomorrow(group=db.get_group(user_id=user[0]))
                try:
                    context.bot.send_message(chat_id=user[0], text=text,
                                             reply_markup=keyboards.menu_names(user_id=user[0]))
                except Exception as e:
                    logger.error(e)
                    context.bot.send_message(chat_id=my_id, text=str(e))
        if (user[2] is not None) and (now.weekday() != 6):  # weather notify
            hours, minutes = map(int, user[2].split(':'))
            notify_time = datetime.datetime.combine(now.date(), datetime.time(hours, minutes))
            if now > notify_time and (now - notify_time).seconds / 60 < 15:
                try:
                    context.bot.send_message(chat_id=user[0], text=weather.get_weather(),
                                             reply_markup=keyboards.menu_names(user_id=user[0]))
                except Exception as e:
                    logger.error(e)
                    context.bot.send_message(chat_id=my_id, text=str(e))


def update_timetable(context, is_hard_forced=False):
    context.bot.send_message(chat_id=my_id, text='checking for update')
    if parser.check_for_update() or is_hard_forced:
        context.bot.send_message(chat_id=my_id, text='starting update')
        try:
            err = parser.main()
        except Exception as e:
            txt = 'from parser : ' + str(e)
            context.bot.send_message(chat_id=my_id, text=txt)
            return
        if len(err) != 0:
            txt = 'Errors ' + str(len(err)) + ':\n' + str(err)
        else:
            txt = 'Update done'
        print(txt)

        context.bot.send_message(chat_id=my_id, text=txt)


def search_review(update, context):
    if 'input_mod' not in context.chat_data:
        context.chat_data['input_mod'] = 'done'

    search_text = 'Введите фамилию преподавателя'
    search_list_text = 'Выберите преподавателя из списка'
    search_error_text = 'Не удалось найти преподавателя с такой фамилией'
    user_id = update.message.chat.id
    if context.chat_data['input_mod'] == 'review_search':
        search_keyboard = reviews.search(surname=update.message.text)
        if search_keyboard:
            context.bot.send_message(chat_id=user_id, text=search_list_text, reply_markup=search_keyboard)
        else:
            context.bot.send_message(chat_id=user_id, text=search_error_text,
                                     reply_markup=keyboards.reviews_menu(context.chat_data['input_mod']))
        return

    context.chat_data['input_mod'] = 'review_search'
    context.bot.send_message(chat_id=user_id, text=search_text,
                             reply_markup=keyboards.reviews_menu(context.chat_data['input_mod']))


def show_reviews(update, context):  # TODO load reviews partly
    user_id = update.message.chat.id
    # context.chat_data['reviews_count'] = 0
    if 'tutor' not in context.chat_data:
        text = 'Произошел сбой. Попробуй еще раз'
        context.bot.send_message(chat_id=user_id, text=text,
                                 reply_markup=keyboards.menu_names(user_id=user_id))
        return
    content = reviews.load_reviews(tutor_id=context.chat_data['tutor'])
    if len(content) == 0:
        text = 'Отзывов пока нет, оставь первый!'
        context.bot.send_message(chat_id=user_id, text=text)
        return
    for review in content:
        context.bot.send_message(chat_id=user_id, text=review['text'], reply_markup=review['keyboard'])


def add_review(update, context):
    user_id = update.message.chat.id
    if not ('tutor' in context.chat_data):
        text = 'Произошел сбой. Попробуй еще раз'
        context.bot.send_message(chat_id=user_id, text=text,
                                 reply_markup=keyboards.menu_names(user_id=user_id))
    if db.check_reviewed(user_id=user_id, tutor_id=context.chat_data['tutor']) == 'Rating':
        text = 'Поставьте оценку'
        context.bot.send_message(chat_id=user_id, text=text,
                                 reply_markup=keyboards.review_rating_keyboard())
    else:
        text = 'Вы уже писали отзыв об этом преподавателе'
        context.bot.send_message(chat_id=user_id, text=text)


def add_review_text(update, context):
    user_id = update.message.chat.id
    if not ('tutor' in context.chat_data):
        text = 'Произошел сбой. Попробуй еще раз'
        context.bot.send_message(chat_id=user_id, text=text,
                                 reply_markup=keyboards.menu_names(user_id=user_id))
    if len(update.message.text) > 1000:
        text = 'Отзыв должен быть короче 1000 символов'
        context.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboards.reviews_menu())
    if reviews.add_review_text(user_id=user_id, tutor_id=context.chat_data['tutor'], text=update.message.text):
        text = 'Спасибо за отзыв!'
        context.chat_data['input_mod'] = 'review_done'
        context.bot.send_message(chat_id=user_id, text=text,
                                 reply_markup=keyboards.reviews_menu(context.chat_data['input_mod']))


def force_force_update(update, context):
    if update.message.chat.id == my_id:
        update_timetable(context, True)


def force_update(update, context):
    if update.message.chat.id == my_id:
        update_timetable(context)


def force_update_weather(update, context):
    if update.message.chat.id == my_id:
        weather.update_weather(context)


def stats(update, context):
    if update.message.chat.id == my_id:
        context.bot.send_message(chat_id=my_id, text=str(db.get_stats()))


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


@ensure_user_db
@ensure_fresh_msg
def start(update, context):
    user_id = update.message.chat.id
    user_name = update.message.chat.first_name
    context.bot.send_message(chat_id=user_id, text='Привет {}. Отправь номер твоей группы'.format(user_name),
                             reply_markup=ReplyKeyboardRemove())
    context.chat_data['input_mod'] = 'number'


@ensure_user_db
@ensure_fresh_msg
def message_input(update, context):
    db.add_to_stats()

    if update.message.chat.type != 'private':
        return

    logger.info((update.message.chat.id, update.message.chat.first_name, update.message.text))

    user_id = update.message.chat.id
    if 'input_mod' not in context.chat_data:
        if db.get_group(user_id=user_id) is None:
            context.chat_data['input_mod'] = 'number'
        else:
            context.chat_data['input_mod'] = 'done'

    if context.chat_data['input_mod'] == 'number':
        group = update.message.text
        if group in groups_lst:
            context.chat_data['input_mod'] = 'done'
            db.set_group_for_user(user_id=user_id, group_id=group)
            menu_keyboard = keyboard = keyboards.menu_names(user_id=user_id)
            context.bot.send_message(chat_id=user_id,
                                     text='Твоя группа – {}. Теперь нажми на кнопку ниже 🔽'.format(group),
                                     reply_markup=menu_keyboard)
            return
        else:
            context.bot.send_message(chat_id=user_id, text='Не могу найти эту группу ☹')
            return

    if context.chat_data['input_mod'] == 'done':
        menu_keyboard = keyboards.menu_names(user_id=user_id)
        group = db.get_group(user_id=user_id)
        if update.message.text == 'Сегодня':
            context.bot.send_message(chat_id=user_id, text=timetable.get_group_today(group=group, user_id=user_id),
                                     reply_markup=menu_keyboard)
            return
        if update.message.text == 'Завтра':
            group = db.get_group(user_id=user_id)
            context.bot.send_message(chat_id=user_id, text=timetable.get_group_tomorrow(group=group, user_id=user_id),
                                     reply_markup=menu_keyboard)
        if update.message.text == 'Неделя':
            context.bot.send_chat_action(chat_id=user_id, action=telegram.ChatAction.TYPING)
            group = db.get_group(user_id=user_id)
            context.bot.send_message(chat_id=user_id, text=timetable.get_group_week(group=group, user_id=user_id),
                                     reply_markup=menu_keyboard)
        if update.message.text == 'Сменить группу':
            context.bot.send_message(chat_id=user_id, text='Отправь номер твоей группы',
                                     reply_markup=ReplyKeyboardRemove())
            context.chat_data['input_mod'] = 'number'
        if update.message.text == 'Канал':
            context.bot.send_message(chat_id=user_id, text='Канал с новостями о разработке бота @NSUlog',
                                     reply_markup=menu_keyboard)
        if update.message.text.split(' ')[0] == 'Погода':
            temp_text = weather.get_weather()
            context.bot.send_message(chat_id=user_id, text=temp_text, reply_markup=menu_keyboard)
        if update.message.text == 'Редактировать':
            context.bot.send_message(chat_id=user_id, text='На какой день изменить расписание ?',
                                     reply_markup=keyboards.day_selection_keyboard())
        if update.message.text.find('Назад') != -1:
            context.bot.send_message(chat_id=user_id, text='⬅', reply_markup=menu_keyboard)
        if update.message.text.find('Отзывы') != -1:
            search_review(update, context)
            return

    if context.chat_data['input_mod'].find('review') != -1:
        if update.message.text.find('Назад') != -1 and context.chat_data['input_mod'].find('text') == -1:
            context.bot.send_message(chat_id=user_id, text='⬅',
                                     reply_markup=keyboards.menu_names(user_id=user_id))
            context.chat_data['input_mod'] = 'done'
            return
        if update.message.text.find('написать отзыв') != -1:
            add_review(update, context)
            return
        if update.message.text.find('Посмотреть отзывы') != -1:
            show_reviews(update, context)
            return
        if context.chat_data['input_mod'].find('search') != -1:
            search_review(update, context)
            return
        if context.chat_data['input_mod'].find('text') != -1:  # review with text
            if update.message.text.find('Назад') != -1:
                context.chat_data['input_mod'] = 'review_done'
                text = 'Спасибо за отзыв!'
                context.bot.send_message(chat_id=user_id, text=text,
                                         reply_markup=keyboards.reviews_menu(context.chat_data['input_mod']))
            else:
                add_review_text(update, context)
            return
    if context.chat_data['input_mod'].find('editing') != -1:
        msg_text = misc.format_text(update.message.text)
        if context.chat_data['input_mod'].find('1') != -1:
            context.chat_data['edit_timetable']['subject'] = msg_text
        if context.chat_data['input_mod'].find('2') != -1:
            context.chat_data['edit_timetable']['tutor'] = msg_text
        if context.chat_data['input_mod'].find('3') != -1:
            context.chat_data['edit_timetable']['room'] = msg_text
        text = misc.editing_text(context)
        group_id = db.get_group(user_id=user_id)
        context.bot.send_message(text=text, chat_id=user_id, reply_markup=keyboards.editing_keyboard(context.chat_data['edit_timetable']))
        context.chat_data['input_mod'] = 'done'


def main(production):
    db.PRODUCTION = production
    load_dotenv(".env")
    if production:
        TOKEN = os.environ.get('PRODUCTION_TOKEN')
    else:
        TOKEN = os.environ.get('DEVELOP_TOKEN')

    updater = Updater(token=TOKEN, use_context=True)
    updater.job_queue.run_repeating(update_timetable, datetime.timedelta(minutes=60 * 24 * 1), context=updater)
    updater.job_queue.run_repeating(weather.update_weather, datetime.timedelta(minutes=15),
                                    first=get_notify_first_check(15) - 60, context=0)
    updater.job_queue.run_repeating(send_notification, datetime.timedelta(minutes=15),
                                    first=get_notify_first_check(15), context=updater)

    ###updater.job_queue.run_once(send_msg_to_all, when=0)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('sub_weather', set_weather_notify))
    updater.dispatcher.add_handler(CommandHandler('force_update', force_update))
    updater.dispatcher.add_handler(CommandHandler('force_force_update', force_force_update))
    updater.dispatcher.add_handler(CommandHandler('update_weather', force_update_weather))
    updater.dispatcher.add_handler(CommandHandler('review', search_review))
    updater.dispatcher.add_handler(CommandHandler('sub', sub_to_notify))
    updater.dispatcher.add_handler(CommandHandler('stats', stats))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, message_input))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))

    updater.dispatcher.add_handler(CallbackQueryHandler(buttons))

    dep = updater.dispatcher

    dep.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main(production=True)

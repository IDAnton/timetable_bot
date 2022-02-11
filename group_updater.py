import requests
import bs4
import logging
import collections
import json
import time

import custom_timetable
import db


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('eg')

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'task',
        'options',
    ),
)


class Client():
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Accept-Language': 'ru',}

        #self.session.headers = {
        #    'User-Agent': 'Mozilla/6.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.90 Safari/537.36',
        #    'Accept-Language': 'ru',}
            
        
        self.result = []

    def get_last_update_time(self):
        try:
            url = 'https://table.nsu.ru/'
            raw = self.session.get(url=url)
            raw.raise_for_status()
            soup = bs4.BeautifulSoup(raw.text)
            return soup.select("div.date-update")[0].contents[0]
        except Exception as e:
            print(f"{e}\nERROR while checking last update")
            return ""

    def load_page(self, group):
        print('page', group)
        url = 'https://table.nsu.ru/group/' + group
        res = self.session.get(url=url)
        res.raise_for_status()
        return res.text

    def parse_page(self, text, gr):
        soup = bs4.BeautifulSoup(text)
        container = soup.select('table.time-table')
        for block in container:
            self.parse_block(block=block, gr_name=gr)

    def parse_block(self, block, gr_name):
        res_dict = {'Понедельник': [], 'Вторник': [], 'Среда': [], 'Четверг': [], 'Пятница': [], 'Суббота': []}
        lessons = block.select('td')
        counter = 1
        for lesson in lessons:
            cells = lesson.select('div.cell')
            type_lst, type = [], []
            subject_lst, subject = [], []
            tutor_lst, tutor = [], []
            room_lst, room = [], []
            week_lst, week = [], []
            for cell in cells:
                if cell.find('div', class_='subject'):
                    subject = cell.find('div', class_='subject').contents[0].strip()
                    type = cell.find('span', class_='type').contents[0] if cell.find('span',
                                                                                     class_='type') else ''
                    if cell.select('div.room')[0].find('a'):
                        room = cell.select('div.room')[0].find('a').contents[0]
                    else:
                        room = cell.find('div', class_='room').contents[0].strip()
                    tutor = cell.find('a', class_='tutor').contents[0] if cell.find('a',
                                                                                    class_='tutor') is not None else ''
                    week = cell.find('div', class_='week').contents[0] if cell.find('div',
                                                                                    class_='week') is not None else ''

                type_lst.append(type)
                subject_lst.append(subject)
                tutor_lst.append(tutor)
                room_lst.append(room)
                week_lst.append(week)

            if counter % 7 == 2:
                res_dict['Понедельник'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            if counter % 7 == 3:
                res_dict['Вторник'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            if counter % 7 == 4:
                res_dict['Среда'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            if counter % 7 == 5:
                res_dict['Четверг'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            if counter % 7 == 6:
                res_dict['Пятница'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            if counter % 7 == 0:
                res_dict['Суббота'].append(
                    {'subject': subject_lst, 'room': room_lst, 'type': type_lst, 'tutor': tutor_lst,
                     'week': week_lst})
            counter += 1

        new_json = json.dumps(res_dict, ensure_ascii=False)
        old_json = db.get_group_content(group_id=str(gr_name))
        if new_json != old_json:
            db.set_group(group_id=str(gr_name), group_content=new_json)
        custom_timetable.update_custom(json.loads(new_json), gr_name)

    def run(self):
        f = open('gr.txt', 'r', encoding='cp1252')
        #f = open('gr.test.txt', 'r', encoding='cp1252')
        errors = []
        groups = []
        groups.append(f.read())
        groups = (groups[0].split('\n'))
        for i in range(len(groups)):
            groups[i] = groups[i].replace('и','i').replace('а','a').replace('м','m').replace('с','s').replace('б','b')

        for group in groups:
            try:
                text = self.load_page(group=str(group))
                self.parse_page(text=text, gr=str(group))
            except Exception as e:
                errors.append(group)
                print('ОШИБКА', e)
            #time.sleep(1)

        return errors


def main():
    parser = Client()
    res = parser.run()
    return res


def check_for_update():
    parser = Client()
    res = parser.get_last_update_time()
    if str(res).lower().find("сегодня") != -1:  # updated today
        return True
    return False


if __name__ == '__main__':
    main()

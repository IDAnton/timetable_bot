import requests
import bs4
import time


def urls_to_names():
    session = requests.Session()
    session.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41',
                'Accept-Language': 'ru',}

    data_file = open('tutors_urls.txt', 'r')
    out_file = open('tutors_list.txt', 'w+')
    urls = []
    for line in data_file:
        urls.append(line)

    progress = 0
    max_progress = len(urls)
    for url in urls:
        text = session.get(url=url).text
        soup = bs4.BeautifulSoup(text)
        name = soup.find('title').contents[0].split('|')[0][:-1:] + '\n'
        out_file.write(name)
        print(round(progress/max_progress, 2))
        progress += 1
        time.sleep(1)

    data_file.close()
    out_file.close()


def tutor_serializer():
    file = open('tutors_parser/tutors_list.txt', 'r')
    res = []
    for tutor in file:
        tutor = tutor.replace('\n', '')
        if tutor.find('.') != -1:
            tmp = tutor.split('.')
            patronymic = tmp[1]
            surname, name = tmp[0].split()
        else:
            if len(tutor.split(' ')) == 2:
                surname, name = tutor.split(' ')
                patronymic = 'None'
            else:
                surname, name, patronymic = tutor.split(' ')[0:3:]
        res.append({'name': name, 'surname': surname, 'patronymic': patronymic})
    file.close()
    return res


def main():
    tutor_serializer()


if __name__ == '__main__':
    main()











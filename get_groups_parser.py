import requests
import bs4
import logging
import collections


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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 YaBrowser/20.2.0.1043 Yowser/2.5 Safari/537.36',
            'Accept-Language': 'ru',}
        self.result = []

    def load_page(self, page):
        url = 'https://table.nsu.ru/faculty/' + str(page)
        res = self.session.get(url=url)
        res.raise_for_status()
        return res.text

    def parse_page(self, text):
        soup = bs4.BeautifulSoup(text)
        container = soup.select('#schedule-degree1')

        for block in container:
            self.parse_block(block=block)

    def parse_block(self, block):
        f = open('gr.txt', 'a')
        groups = block.select('a.group')
        if not groups:
            logger.error('no task')
        for gr in groups:
            print(gr.contents[0])
            f.write(gr.contents[0] + '\n')
        f.close()

    def run(self):
        facs = ['ci','ggf','gi','imp','iphp','mmf','fen','fit','ff','ef']
        for fac in facs:
            print(str(fac))
            text = self.load_page(page=fac)
            self.parse_page(text=text)


if __name__ == '__main__':
    parser = Client()
    parser.run()

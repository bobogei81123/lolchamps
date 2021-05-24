import json
import requests
from bs4 import BeautifulSoup
import urllib
from collections import Counter, defaultdict
from tqdm import tqdm
import shelve

CHAMPIONS_URL = ('http://ddragon.leagueoflegends.com/'
                 'cdn/11.8.1/data/en_US/champion.json')


def get_champions_list():
    js = requests.get(CHAMPIONS_URL).json()
    return list(js['data'].keys())


CHAMPIONS = get_champions_list()

SHELVE = shelve.open('html_cache')


def get_soup(url):
    if url not in SHELVE:
        text = requests.get(url).text
        SHELVE[url] = text

    text = SHELVE[url]
    soup = BeautifulSoup(text, 'html.parser')
    return soup


class Extractor:
    def __init__(self):
        self.banned = defaultdict(Counter)
        self.picked = defaultdict(Counter)
        self.patches = Counter()

    def crawl_games(self, name):
        base_url = 'https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame'
        data = {
            'pfRunQueryFormName': 'MatchHistoryGame',
            'MHG[preload]':  'Tournament',
            'MHG[tournament]': name,
            'MHG[ascending][is_checkbox]': True,
            'MHG[textonly][is_checkbox]': True,
            'MHG[textonly][value]': 1,
            'wpRunQuery': 'Run query',
            'MHG[limit]': 1000
        }
        url = base_url + '?' + urllib.parse.urlencode(data)
        soup = get_soup(url)
        trs = soup.find(id='mw-content-text').find('table').find_all('tr')
        success_count = 0

        for tr in trs:
            tds = tr.find_all('td')
            if not tds:
                continue

            patch = tds[1].text.strip()
            if not patch:
                patch = '__unknown__'
            self.patches[patch] += 1

            ban0, ban1, pick0, pick1 = (list(td.text.split(','))
                                        for td in tds[5:9])
            for champs in (ban0, ban1):
                for champ in champs:
                    self.banned[champ][patch] += 1
            for champs in (pick0, pick1):
                for champ in champs:
                    self.picked[champ][patch] += 1
            success_count += 1

        return success_count

    def dump(self, filename):

        def patch_key_func(p):
            p = p[0]
            if '.' not in p:
                return (-1, -1)
            x, y = p.split('.')
            return (int(x), int(y))

        patches = [{'patch': patch, 'count': count}
                   for patch, count in sorted(self.patches.items(),
                                              key=patch_key_func)]
        data = {
            'banned': self.banned,
            'picked': self.picked,
            'patches': patches,
        }
        with open(filename, 'w') as f:
            json.dump(data, f)


extractor = Extractor()


def absolute_url(url):
    return 'https://lol.fandom.com' + url


def crawl_tournament(url):
    soup = get_soup(url)

    a = soup.find('a', text='Match History')
    if a is None:
        return
    title = a['title']
    if 'does not exist' in title:
        return
    href = a['href']

    url = absolute_url(href)
    soup = get_soup(url)
    tournament_name = (soup
                       .find(id='mw-content-text')
                       .find('table', class_='mhgame')
                       .find('tr')
                       .find('th')
                       .find('a')
                       .text)
    success_count = extractor.crawl_games(tournament_name)
    return (tournament_name, success_count)


def crawl_region(url):
    soup = get_soup(url)

    table = soup.find(text='Main Events').find_next('table')
    trs = table.find_all('tr')

    t = tqdm(trs)

    for tr in t:
        tds = tr.find_all('td')
        if not tds:
            continue

        href = tds[2].find('a')['href']
        url = absolute_url(href)
        result = crawl_tournament(url)
        if result is None:
            continue

        name, count = result
        t.write(f'{name} => {count} games')


def crawl_all_regions():
    regions = [
        'League_Championship_Series',
        'LoL_European_Championship',
        'League_of_Legends_Champions_Korea',
        'LoL_Pro_League',
    ]

    for region in regions:
        href = '/wiki/' + region
        url = absolute_url(href)
        crawl_region(url)


def crawl_all_international():
    for name in ('World_Championship', 'Mid-Season_Invitational'):
        url = 'https://lol.fandom.com/wiki/Portal:Tournaments/International'
        soup = get_soup(url)
        table = soup.find(id=name).find_next('table')
        trs = table.find_all('tr')

        t = tqdm(trs)
        for tr in t:
            td = tr.find_all('td')[2]
            a = td.find('a')
            if a is None:
                continue
            href = a['href']
            url = absolute_url(href)
            result = crawl_tournament(absolute_url(href))

            if result is not None:
                name, count = result
                t.write(f'{name} => {count} games')
                continue

            for sub in ('Main_Event', 'Play-In'):
                url = absolute_url(href + '/' + sub)
                result = crawl_tournament(url)

                if result is None:
                    continue

                name, count = result
                t.write(f'{name} => {count} games')


crawl_all_regions()
crawl_all_international()
extractor.dump('data.json')
SHELVE.close()

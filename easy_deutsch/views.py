import re
from urllib.parse import quote_plus

import pydash
import requests
from bs4 import BeautifulSoup

from django.shortcuts import render

from py_translator import Translator

patterns = [re.compile(f"var c{i}Arr = new Array\((.*)\);")
            for i in range(1, 3)]


def get_context(word):
    if not word:
        return

    headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"}

    res = requests.get(f'https://dict.leo.org/englisch-deutsch/{word}', headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')

    result = soup.select_one('div[data-dz-search="result"]')

    # TODO: suggestion

    search_term = result.get('data-leo-search-term') or word
    word_info = dict(word=search_term, en=[], de=[])

    tables = result.select('div > table')

    for entry in tables[0].select('tbody > tr[data-dz-ui="dictentry"]'):
        for lang in ('en', 'de'):
            data = entry.select_one(f'td[lang="{lang}"]')
            if data:
                word_info[lang].append(data.text)

    # example sentences
    for entry in result.select('[data-dz-name="example"] > table > tbody > tr[data-dz-ui="dictentry"]'):
        for lang in ('en', 'de'):
            data = entry.select_one(f'td[lang="{lang}"]')
            if data:
                word_info[lang].append(data.text)

    # korean
    if word_info['en']:
        korean = Translator().translate(text=word_info['en'][0], dest='ko')
        word_info['ko'] = [korean.text]

    # TODO: search_term에 article 붙이기
    # https://pixabay.com/api/docs/
    res = requests.get('https://pixabay.com/api/',
                       params=dict(key='10332400-1448498582be2b2e5a39c04ca', q=search_term, lang='de', per_page=12))
    word_info['images'] = pydash.map_(res.json()['hits'],
                                      lambda x: dict(preview=x['previewURL'], large=x['largeImageURL']))

    return dict(word_info=word_info)


def home(request):
    word = request.GET.get('word')
    return render(request, 'home.html', get_context(word))

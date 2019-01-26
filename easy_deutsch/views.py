import json

import requests
from bs4 import BeautifulSoup
from pydash import py_

from django.shortcuts import render

from py_translator import Translator

from .async import run_async


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
    word_info['titles'] = ['english', 'deutsch', 'korean']
    word_info['results'] = []

    for table in tables:
        for entry in table.select('tbody > tr[data-dz-ui="dictentry"]'):
            row = [''] * 3
            for i, lang in enumerate(['en', 'de']):
                data = entry.select_one(f'td[lang="{lang}"]')
                if data:
                    row[i] = data.text
            word_info['results'].append(row)

        if word_info['results']:
            break

    # example sentences
    for entry in result.select('[data-dz-name="example"] > table > tbody > tr[data-dz-ui="dictentry"]'):
        row = [''] * 3
        for i, lang in enumerate(['en', 'de']):
            data = entry.select_one(f'td[lang="{lang}"]')
            if data:
                row[i] = data.text
        word_info['results'].append(row)

    # korean
    if word_info['results']:
        translator = Translator()
        results = run_async(
            lambda t: translator.translate(text=t, src='en', dest='ko'),
            py_.map(word_info['results'], 0)
        )
        for i, korean in enumerate(results):
            word_info['results'][i][-1] = korean.text

    # TODO: search_term에 article 붙이기
    # https://pixabay.com/api/docs/
    res = requests.get('https://pixabay.com/api/',
                       params=dict(key='10332400-1448498582be2b2e5a39c04ca', q=search_term, lang='de', per_page=12))
    word_info['images'] = py_.map(res.json()['hits'],
                                  lambda x: dict(preview=x['previewURL'], large=x['largeImageURL']))

    return dict(word_info=word_info)


def search(request):
    word = request.GET.get('word')
    return render(request, 'search.html', get_context(word))


def home(request):
    word = request.GET.get('word')

    with open('data.json') as f:
        data = json.load(f)

    if word:
        data['token_data'] = py_.filter(data['token_data'], lambda t: t['key'] == word)
        ids = py_(data['token_data']).pluck('ids').flatten().value()
        data['data'] = py_.at(data['data'], *ids)
        for d in data['data']:
            d['de_highlight'] = py_(d['de'].split(' ')).map(
                lambda s: f"<font color='red' class='font-weight-bold'>{s}</font>" if s.lower() == word else s
            ).join(' ').value()

    data['sentences'] = py_.order_by(data['data'], ['-count'])
    return render(request, 'home.html', data)

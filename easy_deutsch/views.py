import json

import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from honey.asyncio import run_async
from pydash import py_

from py_translator import Translator
from random import randint


def translate(words, languages=None):
    languages = languages or ('ko', 'es', 'fr')
    translator = Translator()
    return run_async(lambda l: translator.translate(words, src='en', dest=l), languages)


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
    word_info['titles'] = ['english', 'deutsch', 'korean', 'spanish', 'french']
    word_info['results'] = []

    for table in tables:
        for entry in table.select('tbody > tr[data-dz-ui="dictentry"]'):
            row = [''] * 5
            for i, lang in enumerate(['en', 'de']):
                data = entry.select_one(f'td[lang="{lang}"]')
                if data:
                    row[i] = data.text
            word_info['results'].append(row)

        if word_info['results']:
            break

    # example sentences
    for entry in result.select('[data-dz-name="example"] > table > tbody > tr[data-dz-ui="dictentry"]'):
        row = [''] * 5
        for i, lang in enumerate(['en', 'de']):
            data = entry.select_one(f'td[lang="{lang}"]')
            if data:
                row[i] = data.text
        word_info['results'].append(row)

    # korean, spanish, french
    if word_info['results']:
        languages = ('ko', 'es', 'fr')
        result_list = translate(py_.map(word_info['results'], 0), languages)

        for i, results in enumerate(result_list):
            for j, res in enumerate(results):
                word_info['results'][j][2 + i] = res.text

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
    order = request.GET.get('order') or 'id'

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

    order = "-count" if order == "count" else "id"
    sentences = py_.order_by(data['data'], [order])

    offset = int(request.GET.get('offset') or 0)
    limit = int(request.GET.get('limit') or len(sentences))
    data['sentences'] = sentences[offset:offset + limit]

    return render(request, 'home.html', data)


def sentence(request):
    de, en = py_.at(request.GET, 'de', 'en')
    data = dict(
        languages=['de', 'en', 'es', 'fr', 'ko'],
        translations=dict(de=de, en=en),
        query=dict(de=de, en=en)
    )
    translator = Translator()

    if de:
        text = translator.translate(de, src='de', dest='en').text
        data['translations']['en'] = text
    elif en:
        text = translator.translate(en, src='en', dest='de').text
        data['translations']['de'] = text

    if de or en:
        text = data['translations']['en']
        results = run_async(lambda l: translator.translate(text, src='en', dest=l), data['languages'][2:])

        for i, result in enumerate(results, 2):
            lang = data['languages'][i]
            data['translations'][lang] = result.text

    return render(request, 'sentence.html', data)


def random(request):
    with open('data.json') as f:
        data = json.load(f)

    data = data["data"]
    idx = randint(0, len(data))

    return render(request, 'random.html', data[idx])

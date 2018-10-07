import re
from urllib.parse import quote_plus

import pydash
import requests
from bs4 import BeautifulSoup

from django.shortcuts import render

patterns = [re.compile(f"var c{i}Arr = new Array\((.*)\);")
            for i in range(1, 3)]


def get_context(word):
    if not word:
        return

    headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"}

    # https://www.dict.cc/?s=datei
    res = requests.get('https://www.dict.cc', params=dict(s=word), headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')

    # TODO: ADJ/ADV
    article = soup.select_one('tr[title="article sg | article pl"]')

    if not article:
        # suggestion
        suggestions = None
        for bold in soup.select('td.td2 > b'):
            if 'German Suggestions' in bold.text:
                suggestions = pydash.map_(bold.parent.parent.parent.select('a[rel=nofollow]'),
                                          lambda a: dict(word=a.text, link=f"?word={quote_plus(a.text)}"))
                break

        return dict(suggestions=suggestions)

    article_text = article.text.replace('edit', '').strip()
    word_info = dict(
        word=word,
        info=[
            article_text,
            *pydash.map_(article.next_siblings, lambda s: s.text.replace('edit', '').strip())
        ]
    )

    soup = BeautifulSoup(res.content, 'html.parser')

    for script in soup.find_all('script'):
        script_str = str(script.string)
        match = patterns[0].search(script_str)
        if match:
            for lang, pattern in [
                ('english', patterns[0]),
                ('deutsch', patterns[1])
            ]:
                match = pattern.search(script_str)
                if not match:
                    break

                word_info[lang] = pydash.chain(match.groups()[0].split(',')).map(
                    lambda x: x[1:-1]  # remove quote
                ).compact().take(5).value()

            if 'english' in word_info:
                break

    # https://pixabay.com/api/docs/
    q = ' '.join(article_text.split('|')[0].split()[1:])
    res = requests.get('https://pixabay.com/api/',
                       params=dict(key='10332400-1448498582be2b2e5a39c04ca', q=q, lang='de', per_page=12))
    word_info['images'] = pydash.map_(res.json()['hits'],
                                      lambda x: dict(preview=x['previewURL'], large=x['largeImageURL']))

    return dict(word_info=word_info)


def home(request):
    word = request.GET.get('word')
    return render(request, 'home.html', get_context(word))

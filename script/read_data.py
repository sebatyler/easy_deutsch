import json
import pprint

from pydash import py_

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from somajo import Tokenizer

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('easy-deutsch.json', scope)
gc = gspread.authorize(credentials)
sheet = gc.open("Deutsch Wörter").worksheet('Expressions')

tokenizer = Tokenizer(split_camel_case=True, token_classes=False, extra_info=False)
data = py_(sheet.get_all_values()).filter(lambda r: r[0]).map(lambda r: py_.compact(r)).map(
    lambda r: [py_.capitalize(r[0], strict=False), *r[1:]]
).map(
    lambda r, i: dict(id=i, de=r[0], low=r[0].lower(), tokens=tokenizer.tokenize(r[0].lower()), rest=r[1:])
).value()

token_index = {}

for tokens in py_.pluck(data, 'tokens'):
    for token in tokens:
        if len(token) <= 1:
            continue

        t = token.lower()
        if t not in token_index:
            token_index[t] = dict(
                key=t,
                ids=py_(data).filter(lambda d: t in d['tokens']).pluck('id').value()
            )

token_data = py_(token_index.values()).map(
    lambda d: dict(count=len(d['ids']), **d)
).order_by(['-count', 'key']).value()
pprint.pprint(token_data)

for id_, count in py_(token_data).pluck('ids').flatten().count_by().value().items():
    data[id_]['count'] = count

with open('data.json', 'w') as f:
    json.dump(dict(data=data, token_data=token_data), f, indent=4)

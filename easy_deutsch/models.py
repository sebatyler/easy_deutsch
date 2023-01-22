import json
from random import randint

from django.conf import settings

data_dict = None


def get_data():
    global data_dict

    if data_dict is None:
        with open(settings.BASE_DIR / "data.json") as f:
            data_dict = json.load(f)

    return data_dict


def get_random_row():
    data = get_data()["data"]
    idx = randint(0, len(data))
    return data[idx]

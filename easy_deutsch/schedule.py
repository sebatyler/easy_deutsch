from core.telegram import send_mesage
from easy_deutsch.models import get_random_row


def send_random():
    row = get_random_row()
    sentences = "\n".join([*row["rest"], row["de"]])  # en, ..., de

    send_mesage(sentences)

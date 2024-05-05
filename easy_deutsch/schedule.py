import re
from os import environ
from random import choice

import dotenv
import gspread
import telegram
from oauth2client.service_account import ServiceAccountCredentials

from django.conf import settings

from easy_deutsch.models import get_random_row

dotenv.read_dotenv(settings.BASE_DIR / ".env")

bot = telegram.Bot(environ["TELEGRAM_BOT_TOKEN"])


def send_mesage(text, **kwargs):
    return bot.sendMessage(chat_id=environ["TELEGRAM_BOT_CHANNEL_ID"], text=text, **kwargs)


def send_random():
    row = get_random_row()
    sentences = "\n".join([*row["rest"], row["de"]])  # en, ..., de

    send_mesage(sentences)

    send_random_vocabulary()


def send_random_vocabulary():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("easy-deutsch.json", scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key("1MLrRGwww30yjqpLA32R4Nbplq0N0HkwHyus3x9hd55A").worksheet("Vocabulary")

    # skip the first row
    rows = sheet.get_all_values()[1:]

    # choose a random vocabulary
    row = choice(rows)
    title = f"Vocabulary: *{row[0]}*"
    if row[1]:
        title += f" ({row[1]})"
    title = re.sub(r"([\-.()])", r"\\\1", title)

    conversation = f"{row[2]}\n{row[3]}"

    send_mesage(
        f"{title}\n```\n{conversation}```",
        parse_mode=telegram.ParseMode.MARKDOWN_V2,
    )

from os import environ

import dotenv
import telegram

from django.conf import settings

from easy_deutsch.models import get_random_row

dotenv.read_dotenv(settings.BASE_DIR / ".env")


def send_random():
    row = get_random_row()
    sentences = "\n".join([*row["rest"], row["de"]])  # en, ..., de

    bot = telegram.Bot(environ["TELEGRAM_BOT_TOKEN"])
    print(bot.sendMessage(chat_id=environ["TELEGRAM_BOT_CHANNEL_ID"], text=sentences))

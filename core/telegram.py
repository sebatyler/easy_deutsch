import os

import telegram

bot = telegram.Bot(os.getenv("TELEGRAM_BOT_TOKEN"))


def send_mesage(text, is_markdown=False, **kwargs):
    if is_markdown:
        kwargs["parse_mode"] = telegram.ParseMode.MARKDOWN_V2

    return bot.sendMessage(
        chat_id=os.getenv("TELEGRAM_BOT_CHANNEL_ID"),
        text=text,
        **kwargs,
    )

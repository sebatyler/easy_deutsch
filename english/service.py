import re

from core.google import get_sheet
from core.telegram import send_mesage

from .models import Vocabulary


def update_vocabularies():
    sheet = get_sheet(key="1MLrRGwww30yjqpLA32R4Nbplq0N0HkwHyus3x9hd55A", sheet="Vocabulary")

    # skip the first row
    rows = sheet.get_all_values()[1:]

    vocabularies = {}
    for row in rows:
        word = row[0]
        vocabularies[word] = Vocabulary(word=word, note=row[1], conversation=f"{row[2]}\n{row[3]}".strip())

    for word in Vocabulary.objects.filter(word__in=vocabularies.keys()).values_list("word", flat=True):
        del vocabularies[word]

    Vocabulary.objects.bulk_create(vocabularies.values())

    return vocabularies


def send_random_vocabulary():
    # choose a random vocabulary
    voca = Vocabulary.objects.order_by("?").first()

    title = f"Vocabulary: *{voca.word}*"
    if voca.note:
        title += f" ({voca.note})"
    title = re.sub(r"([\-.()])", r"\\\1", title)

    send_mesage(f"{title}\n```\n{voca.conversation}```", is_markdown=True)

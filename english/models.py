from model_utils.models import TimeStampedModel

from django.db import models


class Vocabulary(TimeStampedModel):
    word = models.CharField(max_length=100)
    note = models.CharField(max_length=255, blank=True, null=True)
    conversation = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Vocabularies"

    def __str__(self):
        return f"Vocabulary({self.id}): {self.word}"

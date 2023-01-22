import telegram

from easy_deutsch.schedule import send_random


class TestSendRandom:
    def test(self, mocker):
        mock_send = mocker.patch.object(telegram.Bot, "sendMessage")

        send_random()

        mock_send.assert_called_once()

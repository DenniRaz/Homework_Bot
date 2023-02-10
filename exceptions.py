class HomeworkError(Exception):
    """Базовый класс для homework исключений."""
    error = ''

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'{self.message}'
        else:
            return f'{self.error}'


class TelegramMessageError(HomeworkError):
    """Исключение возникает при условии сбоя в процессе отпраки сообщения."""
    error = 'Ошибка при отправке сообщения'


class RequestError(HomeworkError):
    """Исключение возникает при условии возникновения ошибки доступа URL."""
    error = 'Ошибка доступа URL'


class JSONError(HomeworkError):
    """Исключение возникает при попытке декодирования JSON"""
    error = 'Ошибка декодирования JSON'


class HomeworkStatusError(HomeworkError):
    """
    Исключение возникает при условии отсутсвия выявленного
    статуса работы в словаре HOMEWORK_VERDICTS.
    """
    error = 'В HOMEWORK_VERDICTS нет выявленного статуса работы'

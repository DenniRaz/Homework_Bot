import json
import logging
import os
import time
from http import HTTPStatus

from dotenv import load_dotenv

import requests

import telegram

from exceptions import TokenError, HomeworkStatusError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('homework.log', mode='w', encoding='utf-8')
formatter = logging.Formatter('%(name)s [%(funcName)s] %(asctime)s [%(levelname)s]: %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено')
    except Exception as error:
        logger.error('Ошибка при отправке сообщения')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса Практикум.Домашка."""
    try:
        homework_statuses = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if not homework_statuses.status_code == HTTPStatus.OK:
            logger.error('API домашки возвращает код, отличный от 200')
            raise requests.exceptions.RequestException
        logger.debug('Запрос к API-сервису успешно выполнен')
        return homework_statuses.json()
    except requests.exceptions.RequestException('Ошибка доступа URL') as error:
        logger.error(error, exc_info=True)
        raise error
    except json.decoder.JSONDecodeError as error:
        logger.error(error, exc_info=True)
        raise error


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        logger.error('Ответ API не соответствует формату документации')
        raise TypeError
    elif 'homeworks' not in response:
        logger.error('Ключ homeworks отсутствует в документации')
        raise KeyError
    elif not isinstance(response.get('homeworks'), list):
        logger.error('Значение ключа homeworks не соответствует формату документации')
        raise TypeError
    try:
        homework = response['homeworks']
        return homework[0]
    except IndexError as error:
        logger.error('Список домашних работ пуст')
        raise error


def parse_status(homework):
    """Извлечение информации о конкретной домашней работе."""
    if 'homework_name' not in homework:
        logger.error('homework_name тсутствует в ДЗ')
        raise KeyError
    if 'status' not in homework:
        logger.error('status тсутствует в ДЗ')
        raise KeyError
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        logger.error('В HOMEWORK_VERDICTS нет выявленного статуса работы')
        raise HomeworkStatusError
    verdict = HOMEWORK_VERDICTS.get(f'{status}')
    logger.debug('Выявлен статус работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Переменные окружения недоступны')
        raise TokenError
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            logger.critical(error, exc_info=True)
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

import logging
import os

import time

import requests

import telegram

from dotenv import load_dotenv

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def check_tokens():
    """Проверка доступности переменных окружения"""
    if PRACTICUM_TOKEN is None:
        logging.critical('Нет переменной PRACTICUM TOKEN')
        raise Exception('Нет переменной PRACTICUM TOKEN')
    if TELEGRAM_TOKEN is None:
        logging.critical('Нет переменной TELEGRAM_TOKEN')
        raise Exception('Нет переменной TELEGRAM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        logging.critical('Нет переменной TELEGRAM_CHAT_ID')
        raise Exception('Нет переменной TELEGRAM_CHAT_ID')


def send_message(bot, message):
    """Отправка сообщений в Telegram чат"""
    logging.debug('Сообщение отправлено')
    message = bot.send_message(TELEGRAM_CHAT_ID, message,)
    return message


def get_api_answer(timestamp):
    """Запрос к API"""
    try:
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception:
        logging.exception('Ошибка при запросе к Яндекс API')
    if response.status_code != 200:
        raise Exception(
            f'Ошибка:{response.status_code}'
        )
    return response.json()


def check_response(response):
    """Проверка полученного запроса от API."""
    try:
        response = response['homeworks']
    except KeyError:
        logging.error('Ошибка доступа к ключу')
    if type(response) != list:
        raise TypeError('Данные не в виде списка')
    return response


def parse_status(homework):
    """Статус домашней работы."""
    try:
        hw_name = homework['homework_name']
    except KeyError:
        logging.error('Ошибка доступа к ключу homework_name')

    try:
        homework_status = homework['status']
    except KeyError:
        logging.error('Ошибка доступа к ключу status')

    try:
        hw_verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError:
        logging.error('Неизвестный вердикт')
    return f'Изменился статус проверки работы "{hw_name}". {hw_verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                message = 'Нет обновлений'
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

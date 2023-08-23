import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


def get_soup(response):
    return BeautifulSoup(response.text, features='lxml')


def get_response(session, url):
    try:
        response = session.get(url)
        if response is None:
            error_msg = 'Нет ответа'
            logging.error(error_msg, stack_info=True)
            raise RequestException
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response  # Тесты требуют возврата ответа response из функции
    except RequestException:
        logging.exception(
            'Возникла ошибка при загрузке страницы %s', url,
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if not searched_tag:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def find_all_tag(soup, tag, attrs=None):
    searched_tag = soup.find_all(tag, attrs=(attrs or {}))
    if not searched_tag:
        error_msg = 'Теги %s не найдены', tag
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag

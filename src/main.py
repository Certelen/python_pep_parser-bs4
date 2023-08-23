import logging
import re
from urllib.parse import urljoin
import requests_cache

from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    MAIN_DOC_URL, PEP_DOC_URL, WHATS_NEW_URL, DOWNLOAD_URL,
    BASE_DIR,  # For test
    PYTHON_VERSION_DETAIL_SEARCH, PDF_END_SEARCH,
    EXPECTED_STATUS
)
from outputs import control_output
from utils import find_tag, get_response, find_all_tag, get_soup


def whats_new(session):
    soup = get_soup(get_response(session, WHATS_NEW_URL))
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = find_all_tag(
        div_ul, 'li', attrs={'class': 'toctree-l1'})
    results = [('Ссылка на статью',
                'Заголовок', 'Редактор, Автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(WHATS_NEW_URL, href)
        soup = get_soup(get_response(session, version_link))
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((
            version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    soup = get_soup(get_response(session, MAIN_DOC_URL))
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = find_all_tag(sidebar, 'ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = find_all_tag(ul, 'a')
            break
    results = [('Ссылка на статью',
                'Заголовок', 'Редактор, автор')]
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(PYTHON_VERSION_DETAIL_SEARCH, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    soup = get_soup(get_response(session, DOWNLOAD_URL))
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_tag = find_tag(table_tag, 'a', {'href': re.compile(PDF_END_SEARCH)})
    pdf_link = pdf_tag['href']
    archive_url = urljoin(DOWNLOAD_URL, pdf_link)
    # Тесты не видят папку DOWNLOAD_DIR из constaints
    DOWNLOAD_DIR = BASE_DIR / 'downloads'
    filename = archive_url.split('/')[-1]
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOAD_DIR / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    # По тестам эта функция не может ничего возвращать.
    logging.info(
        f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    status_dict = {'Status': 'Quantity'}
    total_pep = 0
    soup = get_soup(get_response(session, PEP_DOC_URL))
    pep_list = find_tag(soup, 'section', {'id': 'numerical-index'})
    pep_numerical_list = find_tag(
        pep_list, 'table', {'class': 'pep-zero-table docutils align-default'})
    pep_elem = find_all_tag(pep_numerical_list.tbody, 'tr')
    for pep_doc in tqdm(pep_elem):
        zero_status = find_tag(pep_doc, 'td').text[1:]
        pep_link = find_tag(
            pep_doc, 'a', {'class': 'pep reference internal'})['href']
        pep_url = urljoin(PEP_DOC_URL, pep_link)
        soup = get_soup(get_response(session, pep_url))
        doc_status = find_tag(soup, 'abbr').text
        if doc_status not in EXPECTED_STATUS:
            EXPECTED_STATUS[zero_status] = doc_status
        if doc_status != EXPECTED_STATUS[zero_status]:
            logging.error('Несовпадающий статус:')
            logging.info('%u\nСтатус в карточке: %o\nОжидаемые статусы: %d',
                         pep_url, zero_status, doc_status)
        status_dict[doc_status] = status_dict.setdefault(doc_status, 0) + 1
        total_pep += 1
    status_dict['Total'] = total_pep
    result = []
    for status in status_dict:
        result.append([status, status_dict[status]])
    return result


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(
        'Аргументы командной строки: %s', args)
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    logging.info('Парсер запущен!')
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)


if __name__ == '__main__':
    main()

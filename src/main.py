import logging
import re
import requests_cache

from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_DOC_URL
from outputs import control_output
from utils import find_tag, get_response

whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')


def whats_new(session):
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_ul.find_all('li', attrs={'class': 'toctree-l1'})
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((
            version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_tag = find_tag(table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_link = pdf_tag['href']
    archive_url = urljoin(downloads_url, pdf_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    wrong_status_list = []
    status_dict = {'Status': 'Quantity'}
    total_pep = 0
    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    pep_list = find_tag(soup, 'section', {'id': 'numerical-index'})
    pep_numerical_list = find_tag(
        pep_list, 'table', {'class': 'pep-zero-table docutils align-default'})
    pep_elem = pep_numerical_list.tbody.find_all('tr')
    for pep_doc in tqdm(pep_elem):
        zero_status = find_tag(pep_doc, 'td').text[1:]
        pep_link = find_tag(
            pep_doc, 'a', {'class': 'pep reference internal'})['href']
        pep_url = urljoin(PEP_DOC_URL, pep_link)
        response = get_response(session, pep_url)
        soup = BeautifulSoup(response.text, features='lxml')
        doc_status = find_tag(soup, 'abbr').text
        if doc_status not in EXPECTED_STATUS[zero_status]:
            wrong_status_list.append((
                pep_url, EXPECTED_STATUS[zero_status], doc_status))
        status_dict[doc_status] = status_dict.setdefault(doc_status, 0) + 1
        total_pep += 1

    if wrong_status_list:
        print('Несовпадающие статусы:')
        for wrong_status in wrong_status_list:
            print(f'{wrong_status[0]}')
            print(f'Статус в карточке: {wrong_status[1]}')
            print(f'Ожидаемые статусы: {wrong_status[2]}')
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
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()

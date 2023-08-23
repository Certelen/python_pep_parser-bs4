import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (
    DATETIME_FORMAT, OUTPUT_MODE, OUTPUT_FUNCTION,
    BASE_DIR  # For tests
)


def control_output(results, cli_args):
    output = cli_args.output
    if output:
        output_num = 0
        while output != OUTPUT_MODE[output_num]:
            output_num += 1
        message = eval(OUTPUT_FUNCTION[output_num])(results, cli_args)
    else:
        default_output(results)
        return
    if message:
        logging.info(
            'Файл с результатами был сохранён: %s', message)
    logging.info('Парсер завершил работу.')


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results, cli_args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    # По тестам эта функция не может ничего возвращать.
    RESULT_DIR = BASE_DIR / 'results'
    RESULT_DIR.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = RESULT_DIR / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)
    return file_path

from pathlib import Path
from urllib.parse import urljoin

MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_DOC_URL = 'https://peps.python.org/'
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
DOWNLOAD_URL = urljoin(MAIN_DOC_URL, 'download.html')
PYTHON_VERSION_DETAIL_SEARCH = (
    r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)')
PDF_END_SEARCH = r'.+pdf-a4\.zip$'
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
OUTPUT_MODE = ('pretty', 'file')
OUTPUT_FUNCTION = ('pretty_output', 'file_output')
EXPECTED_STATUS = {}

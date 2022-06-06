import os

import cv2
from numpy import ndarray

DATE_FORMAT = '%Y-%m-%d'  # 2021-10-15
DATE_HOUR_FORMAT = f'{DATE_FORMAT}-%H'  # 2021-10-15-16
DATE_FORMAT_ON_POSTCARD = '%a, %d %b'  # Fri, 15 Oct

PATH_TO_SAVE_TEST_POSTCARDS = 'external_data/test_postcards'
PATH_TO_POSTCARD_SAMPLES = 'external_data/postcard_samples'
DEFAULT_PATH_TO_SAVE_POSTCARD = 'external_data/weather_postcards'

ICONS_PATH = 'external_data/weather_img'

DATABASE_NAME = 'weather.db'


def get_norm_and_join_path(*args: str) -> str:
    return os.path.normpath(os.path.join(*args))


def get_image(weather_type: str) -> ndarray:
    icon_name = ICONS_DATA[weather_type]['icon_file_name']
    path_to_icon = get_norm_and_join_path(ICONS_PATH, icon_name)
    return cv2.imread(path_to_icon, -1)


ICONS_DATA = {
    'sun': {
        'weather_type': 'Clear',
        'icon_file_name': 'sun.png',
        'colour': '32, 165, 218'
    },
    'rain': {
        'weather_type': 'Possible light rain',
        'icon_file_name': 'rain.png',
        'colour': '225, 105, 65'
    },
    'snow': {
        'weather_type': 'Light snow',
        'icon_file_name': 'snow.png',
        'colour': '235, 206, 135'
    },
    'cloud': {
        'weather_type': 'Foggy',
        'icon_file_name': 'cloud.png',
        'colour': '105, 105, 105'
    },
    'no data': {
        'weather_type': 'No data',
        'icon_file_name': '',
        'colour': '255, 255, 255',
    }
}

TEST_POSTCARDS_DATA = (
    (('Partly Cloudy', 'Thu, 14 Oct', '9', get_image('cloud'), (105, 105, 105)), '14_oct.jpg'),
    (('Possible Light Rain', 'Sat, 16 Oct', '7', get_image('rain'), (225, 105, 65)), '16_oct.jpg'),
)

# ICONS constants
import re

ICON_FILE_NAME = 'icon_file_name'

# WEATHER constants
WEATHER_TYPE = 'weather_type'

# POSTCARD weather types wordings
CLEAR, RAIN = 'Clear', 'rain'
SUN, SNOW = 'sun', 'snow'
CLOUD, NO_DATA = 'cloud', 'no data'

# paths
TEMPLATE_PATH = 'external_data/template.jpg'
PATH_TO_SAVE_TEST_POSTCARDS = 'external_data/test_postcards'
PATH_TO_POSTCARD_SAMPLES = 'external_data/postcard_samples'
DEFAULT_PATH_TO_SAVE_POSTCARD = 'external_data/weather_postcards'
ICONS_PATH = 'external_data/weather_img'

# icons paths
SUN_ICON_PATH = 'sun.png'
RAIN_ICON_PATH = 'rain.png'
SNOW_ICON_PATH = 'snow.png'
CLOUD_ICON_PATH = 'cloud.png'

# RegEx
SUNNY_PATTERN = re.compile(r'clear|sun')
RAINY_PATTERN = re.compile(r'drizzle|rain')
SNOW_PATTERN = re.compile(r'snow')
CLOUDY_PATTERN = re.compile(r'overcast|cloud|foggy')

# url data
BASE_URL = "https://darksky.net/details"
SPB_COORDS = '59.9343,30.3351'

# COLORS
COLOR = 'color'
BLACK_COLOR = (0, 0, 0)

# DATE formats
DATE_FORMAT = '%Y-%m-%d'  # 2021-10-15
DATE_HOUR_FORMAT = f'{DATE_FORMAT}-%H'  # 2023-03-15-16
DATE_FORMAT_ON_POSTCARD = '%a, %d %b'  # Wed, 15 Mar

# icons data
ICONS_DATA = {
    SUN: {
        WEATHER_TYPE: CLEAR,
        ICON_FILE_NAME: SUN_ICON_PATH,
        COLOR: '32, 165, 218'
    },
    RAIN: {
        WEATHER_TYPE: 'Possible light rain',
        ICON_FILE_NAME: RAIN_ICON_PATH,
        COLOR: '225, 105, 65'
    },
    SNOW: {
        WEATHER_TYPE: 'Light snow',
        ICON_FILE_NAME: SNOW_ICON_PATH,
        COLOR: '235, 206, 135'
    },
    CLOUD: {
        WEATHER_TYPE: 'Foggy',
        ICON_FILE_NAME: CLOUD_ICON_PATH,
        COLOR: '105, 105, 105'
    },
    NO_DATA: {
        WEATHER_TYPE: NO_DATA.capitalize(),
        ICON_FILE_NAME: '',
        COLOR: '255, 255, 255',
    }
}

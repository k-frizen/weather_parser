# -*- coding: utf-8 -*-
import datetime
import re
import threading
import time
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from settings import ICONS_PATH, ICONS_DATA, DATE_HOUR_FORMAT, get_norm_and_join_path


class WeatherMaker(threading.Thread):
    """Thread-class to parse https://darksky.net and collect forecast"""
    SUNNY_PATTERN = re.compile(r'clear|sun')
    RAINY_PATTERN = re.compile(r'drizzle|rain')
    SNOW_PATTERN = re.compile(r'snow')
    CLOUDY_PATTERN = re.compile(r'overcast|cloud|foggy')

    def __init__(self, lock: threading.Lock, day: datetime.date, res_holder: list):
        super().__init__()
        self.res_holder = res_holder
        self.lock = lock
        self.day = day
        self.weather_resp = requests.get(f'https://darksky.net/details/59.9343,30.3351/{str(self.day)}/ca24/en ')

    def _weather_type_handler(self, weather_type: str) -> Tuple[str, str]:
        """Compares weather type with path to icon and colour belong to this type.
        Returns tuple of colour as BGR string for image and path to weather icon

        :param weather_type: represents forecast option like precipitation, cloudiness or clearness"""

        sunny_match = re.findall(self.SUNNY_PATTERN, weather_type)
        rainy_match = re.findall(self.RAINY_PATTERN, weather_type)
        snow_match = re.findall(self.SNOW_PATTERN, weather_type)
        cloudy_match = re.findall(self.CLOUDY_PATTERN, weather_type)

        if sunny_match:
            key = 'sun'
        elif rainy_match:
            key = 'rain'
        elif snow_match:
            key = 'snow'
        elif cloudy_match:
            key = 'cloud'
        else:
            key = 'no data'

        weather_icon, colour = ICONS_DATA[key]['icon_file_name'], ICONS_DATA[key]['colour']
        icon_path = get_norm_and_join_path(ICONS_PATH, weather_icon)
        return icon_path, colour

    def run(self):
        if self.weather_resp.status_code == 200:
            html_doc = BeautifulSoup(self.weather_resp.text, features='html.parser')
            weather_data = html_doc.find_all('script')
            date_for_searching = int(time.mktime(time.strptime(str(self.day) + '-16', DATE_HOUR_FORMAT)))
            source = re.findall(f'{date_for_searching}.*?"time"', str(weather_data))

            temperature_source = str(re.findall(r'"temperature":.*?,', str(source[0]))[0])
            temperature = str(re.findall(r':\d*.?\d*', temperature_source)[0])[1:]

            weather_match = re.findall(r'"summary":"[\w*\s?]*"', str(source[0]))
            days_difference = (self.day - datetime.date.today()).days

            if weather_match and days_difference < 10:
                weather_type = str(weather_match[0]).split('":"')[1][:-1]
            else:
                weather_type = ICONS_DATA['no data']['weather_type']

            icon, colour = self._weather_type_handler(weather_type.lower())

            data = {
                'weather_type': weather_type,
                'date': self.day,
                'temperature': temperature,
                'icon_path': icon,
                'colours': colour
            }
            with self.lock:
                self.res_holder.append(data)

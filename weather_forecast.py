# -*- coding: utf-8 -*-
import datetime
import threading
import time
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from constants import *
from utils import get_norm_and_joined_path


class WeatherMaker(threading.Thread):
    """A thread class for collecting weather forecast data from https://darksky.net.

    Args:
        lock: A threading.Lock object for synchronizing access to shared resources.
        day: A datetime.date object representing the day to collect forecast data for.
        weather_data: A list to hold the collected weather forecast data."""

    def __init__(self, lock: threading.Lock, day: datetime.date, weather_data: list):
        super().__init__()
        self.weather_data_list = weather_data
        self.lock = lock
        self.day = day
        self.weather_resp = requests.get(f'{BASE_URL}/{SPB_COORDS}/{str(self.day)}/ca24/en ')

    @staticmethod
    def _weather_type_handler(weather_type: str) -> Tuple[str, str]:
        """
        Returns a tuple of path to weather icon and color as BGR string for image, based on
        the provided weather type.

        Args:
            weather_type: A string representing the type of weather forecast.

        Returns:
            A tuple containing the path to the weather icon and the color as a BGR string for the image.
        """

        sunny_match = re.findall(SUNNY_PATTERN, weather_type)
        rainy_match = re.findall(RAINY_PATTERN, weather_type)
        snow_match = re.findall(SNOW_PATTERN, weather_type)
        cloudy_match = re.findall(CLOUDY_PATTERN, weather_type)

        if sunny_match:
            key = SUN
        elif rainy_match:
            key = RAIN
        elif snow_match:
            key = RAIN
        elif cloudy_match:
            key = CLOUD
        else:
            key = NO_DATA

        icon_data = ICONS_DATA[key]
        weather_icon = icon_data[ICON_FILE_NAME]
        color = icon_data[COLOR]
        icon_path = get_norm_and_joined_path(ICONS_PATH, weather_icon)
        return icon_path, color

    def run(self):
        """ Collects the weather forecast data from https://darksky.net and appends it to the res_holder list. """
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
                weather_type = ICONS_DATA[NO_DATA][WEATHER_TYPE]

            icon, color = self._weather_type_handler(weather_type.lower())

            data = {
                WEATHER_TYPE: weather_type,
                'date': self.day,
                'temperature': temperature,
                'icon_path': icon,
                'colors': color
            }
            with self.lock:
                self.weather_data_list.append(data)

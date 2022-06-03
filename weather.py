# -*- coding: utf-8 -*-

import argparse
import datetime
import os.path
import sqlite3
import threading
from typing import Tuple, Iterable, List

import cv2
from numpy import ndarray

from base import Forecast
from weather_forecast import WeatherMaker


class ImageMaker:
    """The postcard Factory.

    This class prepares data from database to cover it postcard; draws a gradient on postcard;
    compares icon and postcard with gradient and text (date, temperature, weather)"""

    def __init__(self):
        self.__width, self.__height = 0, 0

    @staticmethod
    def viewImage(image, name_of_window):
        """Provide display postcard"""
        cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
        cv2.imshow(name_of_window, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def compare_background_and_icon(self, background: ndarray, icon: ndarray, colour: tuple) -> ndarray:
        """Compares postcard and icon overwriting pixels from icon to postcard.

        :param background: postcard background matrix
        :param icon: icon matrix
        :param colour: first colour in range gradient
        :return: postcard with gradient and weather icon
        """
        self.__draw_gradient(background, colour)
        x, y = self.__width // 4, self.__height // 2
        b, g, r, a = cv2.split(icon)
        overlay_color = cv2.merge((b, g, r))

        mask = cv2.medianBlur(a, 5)
        h, w, _ = overlay_color.shape
        roi = background[y:y + h, x:x + w]

        # Black-out the area behind the logo in our original ROI
        img1_bg = cv2.bitwise_and(roi.copy(), roi.copy(), mask=cv2.bitwise_not(mask))
        # Mask out the logo from the logo image.
        img2_fg = cv2.bitwise_and(overlay_color, overlay_color, mask=mask)
        background[y:y + h, x:x + w] = cv2.add(img1_bg, img2_fg)

        return background

    def draw_postcard(self, data: tuple, path_to_save: str):
        """Draws picture with colored background, degrees, date and weather type caption. Display result postcard and
        save it.

        :param data: database field contains weather type and temp at this date, icon path and colour to draw gradient
        :param path_to_save: directory where weather postcards will be stored."""
        postcard_template = cv2.imread('external_data/template.jpg')
        weather_type, date, temp, icon, colour = data

        postcard_side = max(postcard_template.shape[:2])
        resized_icon_shape = int(postcard_side * .4)

        postcard_background = cv2.resize(postcard_template, (postcard_side, postcard_side))

        self.__width, self.__height = postcard_background.shape[:2]
        assert self.__width == self.__height == postcard_side
        if icon is not None:
            resized_icon = cv2.resize(icon, (resized_icon_shape, resized_icon_shape))
            background = self.compare_background_and_icon(postcard_background, resized_icon, colour)
        else:
            background = postcard_background

        x_coord_for_text = int(self.__width * .2) if len(weather_type) < 10 else int(self.__width * .1)
        cv2.putText(background, f"{weather_type}, {temp} deg",  # write a weather type and temperature
                    (x_coord_for_text, int(self.__height * .2)), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 0), 1)

        cv2.putText(background, date,  # write a date in "weekday, day month" format
                    (int(self.__width * .2), int(self.__height * .4)), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 0), 1)

        self.viewImage(background, 'postcard')

        #  save the postcard
        file_name = "_".join(date.split()[1:]).lower()  # dd_mmm (01_jan, 30_oct, ect)
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        cv2.imwrite(os.path.normpath(os.path.join(path_to_save, f'{file_name}.jpg')), background)

    def __draw_gradient(self, background: ndarray, colour: tuple):
        """Gradient will be drawn from colour depends of weather type.

        :param background: the picture to draw on it
        :param colour: gradient will be from this colour to white."""
        steps = [(255 - c) / self.__width for c in colour]
        for x in range(self.__width):
            cv2.line(background, (x, 0), (x, self.__height), colour, 1)
            colour = [c + step for c, step in zip(colour, steps)]


class DatabaseUpdater:
    """Class updates database: inserts and extracts data."""

    def __init__(self):
        self.conn = sqlite3.connect('weather.db')
        self.conn.text_factory = bytes

    def get_data_from_db(self, starts_from: datetime.date = None, to: datetime.date = None):
        """Extracts data from database in dates range from date_range param and returns it.

        :param starts_from: first date of diapason used to get forecast
        :param to: last date of diapason used to get forecast
        :rtype: List[Tuple[str, str, str, ndarray, Tuple[int, int, int]]]
        """
        first_day = starts_from or datetime.date.today() - datetime.timedelta(weeks=1)
        last_day = to or datetime.date.today() + datetime.timedelta(days=10)
        res = Forecast.select().where(Forecast.date.between(first_day - datetime.timedelta(days=1),
                                                            last_day - datetime.timedelta(days=1)))
        self.conn.close()
        return [self.__unpack_data((field.weather_type, field.date, field.temperature, field.icon_path, field.colours))
                for field in res]

    def save_weather_to_db(self, forecast: list):
        """Saves forecasts to database and commit changes

        :param forecast: forecasts collected by parser"""
        self.insert_data(forecast)
        self.conn.commit()

    @staticmethod
    def __unpack_data(data: tuple) -> tuple[str, str, str, ndarray, tuple[int, ...]]:
        """Prepares data from database and returns it.

        :param data: field of Forecast table contains weather type and temp at this date, icon path and colour
        :return: prepared data. For example convert date - datetime.date(2021, 11, 7) -> 'Sun, 7 Nov' """
        weather_type, _date, temp, icon_path, colour = data
        date = str(_date.strftime('%a, %d %b'))
        temp = temp.split('.')[0]
        icon = cv2.imread(icon_path, -1) if icon_path else None
        colour = tuple(map(int, colour.split(',')))
        return weather_type, date, temp, icon, colour

    @staticmethod
    def insert_data(data: list):
        """Executes updating (if some fields exists yet)
        or inserting data to database.

        :param data: list with dicts contains forecast"""
        for day_weather in data:
            assert isinstance(day_weather, dict)
            Forecast.insert(**day_weather).on_conflict(
                conflict_target=(Forecast.date,),
                update=day_weather
            ).execute()


class Manager:
    """The base class. Manages all process:

    -Collecting data from website
    -Insert it in database
    -Extract fields of database
    -Send forecasts to ImageMaker class to draw postcards"""

    COUNT_OF_DAYS = 10
    COUNT_OF_WEEKDAYS = 7

    def __init__(self, parameters: str = '', path_to_save: str = 'external_data/weather_postcards'):
        """ line in '-f day1 -l day2 -c -p' format. day must be written as yyyy-mm-dd.

        :param parameters: -c - represents print weather to Console, -p - display Postcard
         """
        self.weather_data = []
        self.parameters, self.path_to_save = parameters, path_to_save

    @staticmethod
    def next_day_gen(date: datetime.datetime, n: int) -> Iterable[datetime.date]:
        """Generates next day in yyyy-mm-dd format

        :param n: count of total days
        :param date: first day to calculate"""
        for _ in range(n):
            yield date.date()
            date += datetime.timedelta(days=1)

    def get_weather_data(self, first_date: datetime.datetime = None, last_date: datetime.datetime = None):
        """Generates dates list to get forecast by dates. Method starts threads parsed forecast website

        :param first_date: first date of diapason used to parse website
        :param last_date: last date of diapason used to parse website"""
        date_start_from = first_date or datetime.datetime.today() - datetime.timedelta(weeks=1)
        count_of_days = (last_date - first_date).days if last_date else self.COUNT_OF_DAYS + self.COUNT_OF_WEEKDAYS
        lock = threading.Lock()

        dates = [date for date in self.next_day_gen(n=count_of_days, date=date_start_from)]
        predictors = [WeatherMaker(lock, day=day, res_holder=self.weather_data) for day in dates]
        for predictor in predictors:
            predictor.start()
        for predictor in predictors:
            predictor.join()

    def __enter_the_dates_range(self) -> Tuple[datetime.datetime, datetime.datetime, bool, bool]:
        """ Method provides user data entry"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', type=str, help='Enter first date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-l', type=str, help='Enter last date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-p', action='store_true', help='indicate param to print and save postcards')
        parser.add_argument('-c', action='store_true', help='indicate param to print forecasts in console')
        dates = parser.parse_args() if self.parameters == '' else parser.parse_args(self.parameters.split())
        return datetime.datetime.strptime(
            dates.f, '%Y-%m-%d'), datetime.datetime.strptime(dates.l, '%Y-%m-%d'), dates.p, dates.c

    def run(self):
        db_updater = DatabaseUpdater()
        first_date, last_date, need_postcards, need_forecast = self.__enter_the_dates_range()
        assert (last_date - first_date).days > 0

        self.get_weather_data(first_date, last_date)
        db_updater.save_weather_to_db(self.weather_data)
        forecast = db_updater.get_data_from_db(first_date, last_date)
        for forecast_data in forecast:
            forecast_text = 'At {} weather is {}, {} degrees'.format(
                forecast_data[1], (forecast_data[0].lower()), forecast_data[2])

            if need_postcards & need_forecast:
                ImageMaker().draw_postcard(forecast_data, self.path_to_save)
                print(forecast_text)
            else:
                print(forecast_text) if need_forecast else ImageMaker().draw_postcard(forecast_data, self.path_to_save)


if __name__ == "__main__":
    Manager('-f 2021-11-11 -l 2021-11-13 -c -p').run()

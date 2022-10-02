# -*- coding: utf-8 -*-

import argparse
import threading
from datetime import datetime, timedelta
from typing import Iterable, Optional

from base import DatabaseUpdater
from postcard import ImageMaker
from settings import DATE_FORMAT, DEFAULT_PATH_TO_SAVE_POSTCARD
from weather_forecast import WeatherMaker


class Manager:
    """The base class. Manages all process:

    -Collecting data from website
    -Insert it in database
    -Extract fields of database
    -Send forecasts to ImageMaker class to draw postcards"""

    COUNT_OF_DAYS = 10
    COUNT_OF_WEEKDAYS = 7

    def __init__(self, parameters: str = '', path_to_save: str = DEFAULT_PATH_TO_SAVE_POSTCARD):
        """ line in '-f day1 -l day2 -c -p' format. day must be written as yyyy-mm-dd.

        :param parameters: -c - represents print weather to Console, -p - display Postcard
        :param path_to_save: directory for saving images
         """
        self.weather_data = []
        self.parameters = parameters
        self.path_to_save = path_to_save

    @staticmethod
    def next_day_gen(date: datetime.date, n: int) -> Iterable[datetime.date]:
        """Generates next day in yyyy-mm-dd format

        :param n: count of total days
        :param date: first day to calculate"""
        for _ in range(n):
            yield date
            date += timedelta(days=1)

    def get_weather_data(self, first_date: Optional[datetime.date] = None,
                         last_date: Optional[datetime.date] = None):
        """Generates dates list to get forecast by dates. Method start to get forecast data by threads.

        :param first_date: first date of diapason used to parse website
        :param last_date: last date of diapason used to parse website"""
        date_start_from = first_date or datetime.today() - timedelta(weeks=1)
        count_of_days = (last_date - first_date).days if last_date else self.COUNT_OF_DAYS + self.COUNT_OF_WEEKDAYS
        lock = threading.Lock()

        dates = [day for day in self.next_day_gen(n=count_of_days, date=date_start_from)]
        predictors = [WeatherMaker(lock, day=day, res_holder=self.weather_data) for day in dates]
        for predictor in predictors:
            predictor.start()
        for predictor in predictors:
            predictor.join()

    def __parse_the_dates_range(self) -> tuple[tuple[datetime.date, ...], bool, bool]:
        """ Method provides user data entry using argparse"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', type=str, help='Enter first date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-l', type=str, help='Enter last date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-p', action='store_true', help='indicate param to print and save postcards')
        parser.add_argument('-c', action='store_true', help='indicate param to print forecasts in console')

        dates = parser.parse_args() if not self.parameters else parser.parse_args(self.parameters.split())
        dates_range = tuple(datetime.strptime(date, DATE_FORMAT).date() for date in (dates.f, dates.l))
        return dates_range, dates.p, dates.c

    def run(self):
        """Main method provides all processes of project"""
        db_updater = DatabaseUpdater()
        (first_date, last_date), need_postcards, need_forecast = self.__parse_the_dates_range()
        assert (last_date - first_date).days > 0

        self.get_weather_data(first_date, last_date)
        db_updater.save_weather_to_db(self.weather_data)
        forecast = db_updater.get_data_from_db(first_date, last_date)
        for forecast_data in forecast:
            forecast_text = 'On {weekday} weather is {weather_type}, {temp} degrees'.format(
                weekday=forecast_data[1], weather_type=forecast_data[0].lower(), temp=forecast_data[2])

            if need_postcards:
                print(forecast_text)

            if need_postcards:
                ImageMaker().draw_postcard(forecast_data, self.path_to_save)


if __name__ == "__main__":
    Manager('-f 2022-08-16 -l 2022-08-17 -c -p').run()

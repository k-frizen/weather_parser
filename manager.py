# -*- coding: utf-8 -*-
"""This module contains the Manager class for managing all processes of the weather forecast project."""
import argparse
import threading
from datetime import datetime, timedelta
from typing import Iterable, Optional

from base import DatabaseUpdater
from constants import DEFAULT_PATH_TO_SAVE_POSTCARD, DATE_FORMAT
from postcard import ImageMaker
from weather_forecast import WeatherMaker


class Manager:
    """The base class that manages the entire weather forecast process, including:

    - Collecting data from the website
    - Inserting the data into the database
    - Extracting fields from the database
    - Sending forecasts to the ImageMaker class to draw postcards

    Attributes:
    ----------
    COUNT_OF_DAYS : int
        The default number of days for which to generate forecasts
    COUNT_OF_WEEKDAYS : int
        The number of days in a week (including weekends), constant

    Parameters:
    ----------
    parameters : str, optional
        The string of command line parameters in the format "-f day1 -l day2 -c -p"
        where "day1" and "day2" are dates in the format "yyyy-mm-dd", and "-c" and "-p"
        indicate whether to print weather to the console and display postcards, respectively
    path_to_save : str, optional
        The directory path for saving images of postcards
    """

    COUNT_OF_DAYS = 10
    COUNT_OF_WEEKDAYS = 7

    def __init__(self, parameters: str = '', path_to_save: str = DEFAULT_PATH_TO_SAVE_POSTCARD):
        """
        Initialize a Manager object with default or given parameters.

        Parameters:
        ----------
        parameters : str, optional
            The string of command line parameters in the format "-f day1 -l day2 -c -p"
            where "day1" and "day2" are dates in the format "yyyy-mm-dd", and "-c" and "-p"
            indicate whether to print weather to the console and display postcards, respectively
        path_to_save : str, optional
            The directory path for saving images of postcards
        """
        self.weather_data = []
        self.parameters = parameters
        self.path_to_save = path_to_save

    @staticmethod
    def next_day_gen(date: datetime.date, n: int) -> Iterable[datetime.date]:
        """Generate an iterable of the next n days after the given date in "yyyy-mm-dd" format.

        Parameters:
        ----------
        date : datetime.date
            The date from which to start generating the iterable
        n : int
            The total number of days to generate

        Returns:
        -------
        An iterable of datetime.date objects representing the next n days after the given date
        """
        for _ in range(n):
            yield date
            date += timedelta(days=1)

    def get_weather_data(self, first_date: Optional[datetime.date] = None,
                         last_date: Optional[datetime.date] = None):
        """Generate a list of dates to get forecasts for and start getting forecast data using threads.

        Parameters:
        ----------
        first_date : datetime.date, optional
            The first date of the date range for which to generate forecasts
        last_date : datetime.date, optional
            The last date of the date range for which to generate forecasts

        Notes:
        -----
        If no dates are specified, the method will use the default date range (10 days + 7 weekdays)
        starting from today's date. The method uses threads to get forecast data for each date in the range.
        """
        date_start_from = first_date or datetime.today() - timedelta(weeks=1)
        count_of_days = (last_date - first_date).days if last_date else self.COUNT_OF_DAYS + self.COUNT_OF_WEEKDAYS
        lock = threading.Lock()

        dates = [day for day in self.next_day_gen(n=count_of_days, date=date_start_from)]
        predictors = [WeatherMaker(lock, day=day, weather_data=self.weather_data) for day in dates]
        for predictor in predictors:
            predictor.start()
        for predictor in predictors:
            predictor.join()

    def __parse_the_dates_range(self) -> tuple[tuple[datetime.date, ...], bool, bool]:
        """
        Parses user input for date range and other parameters using argparse.

        Returns:
        Tuple containing the date range as a tuple of datetime.date objects, a boolean indicating whether postcards
        should be printed and saved, and a boolean indicating whether forecast data should be printed to console.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', type=str, help='Enter first date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-l', type=str, help='Enter last date of diapason to get forecast in yyyy-mm-dd format')
        parser.add_argument('-p', action='store_true', help='indicate param to print and save postcards')
        parser.add_argument('-c', action='store_true', help='indicate param to print forecasts in console')
        import datetime
        dates = parser.parse_args() if not self.parameters else parser.parse_args(self.parameters.split())
        dates_range = tuple(datetime.datetime.strptime(date, DATE_FORMAT).date() for date in (dates.f, dates.l))
        return dates_range, dates.p, dates.c

    def run(self):
        """
        Runs the main processes of the project, including collecting data from the website, inserting it into the
        database, extracting data from the database, and sending forecasts to ImageMaker to draw postcards.

        Returns:
        None
        """
        db_updater = DatabaseUpdater()
        (first_date, last_date), need_postcards, need_forecast = self.__parse_the_dates_range()
        assert (last_date - first_date).days > 0

        self.get_weather_data(first_date, last_date)
        db_updater.save_weather_to_db(self.weather_data)
        forecast = db_updater.get_data_from_db(first_date, last_date)
        for forecast_data in forecast:
            forecast_text = 'On {weekday} weather is {weather_type}, {temp} degrees'.format(
                weekday=forecast_data[1], weather_type=forecast_data[0].lower(), temp=forecast_data[2]
            )
            if need_postcards:
                print(forecast_text)

            if need_postcards:
                ImageMaker(self.path_to_save).draw_postcard(forecast_data)


if __name__ == "__main__":
    import datetime

    today = datetime.date.today()
    day_after_few_days = today + timedelta(days=2)
    day1, day2 = today.strftime(DATE_FORMAT), day_after_few_days.strftime(DATE_FORMAT)
    Manager(f'-f {day1} -l {day2} -c -p').run()

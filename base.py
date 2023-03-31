# -*- coding: utf-8 -*-
import datetime
import sqlite3
from typing import Optional

import cv2
import peewee
from numpy.core.multiarray import ndarray

from constants import DATE_FORMAT_ON_POSTCARD

DATABASE_NAME = 'weather.db'
database = peewee.SqliteDatabase(DATABASE_NAME)


class BaseTable(peewee.Model):
    class Meta:
        database = database


class Forecast(BaseTable):
    date = peewee.DateTimeField(unique=True)
    temperature = peewee.CharField()
    weather_type = peewee.CharField()
    icon_path = peewee.CharField()
    colors = peewee.CharField()


database.create_tables([Forecast])


class DatabaseUpdater:
    """Class updates database: inserts and extracts data."""

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME)
        self.conn.text_factory = bytes

    def get_data_from_db(self, starts_from: datetime.date = None, to: datetime.date = None):
        """Extracts data from database in dates range from date_range param and returns it.

        :param starts_from: first date of diapason used to get forecast
        :param to: last date of diapason used to get forecast
        :rtype: list[tuple[str, str, str, Optional[ndarray], tuple[int, int, int]]]
        """
        first_day = starts_from or datetime.date.today() - datetime.timedelta(weeks=1)
        last_day = to or datetime.date.today() + datetime.timedelta(days=10)
        res = Forecast.select().where(
            Forecast.date.between(
                first_day - datetime.timedelta(days=1), last_day - datetime.timedelta(days=1))
        )
        self.conn.close()
        return [self.__unpack_data((
            field.weather_type, field.date, field.temperature, field.icon_path, field.colors
        ))
            for field in res]

    def save_weather_to_db(self, forecast: list[dict]):
        """Executes updating (if some fields exists yet)
        or inserting data to database.

        :param forecast: forecasts collected by parser"""
        for day_weather in forecast:
            Forecast.insert(**day_weather).on_conflict(
                conflict_target=(Forecast.date,),
                update=day_weather
            ).execute()
        self.conn.commit()

    @staticmethod
    def __unpack_data(data: tuple) -> tuple[str, str, str, Optional[ndarray], tuple[int, ...]]:
        """Prepares data from database and returns it.

        :param data: field of Forecast table contains weather type and temp at this date, icon path and color
        :return: prepared data. For example convert date - datetime.date(2021, 11, 7) -> 'Sun, 7 Nov' """
        weather_type, _date, temp, icon_path, color = data
        date = str(_date.strftime(DATE_FORMAT_ON_POSTCARD))
        temp = temp.split('.')[0]
        icon = cv2.imread(icon_path, -1) if icon_path else None
        color = tuple(map(int, color.split(',')))
        return weather_type, date, temp, icon, color

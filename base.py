# -*- coding: utf-8 -*-

import peewee

database = peewee.SqliteDatabase('weather.db')


class BaseTable(peewee.Model):
    class Meta:
        database = database


class Forecast(BaseTable):
    date = peewee.DateTimeField(unique=True)
    temperature = peewee.CharField()
    weather_type = peewee.CharField()
    icon_path = peewee.CharField()
    colours = peewee.CharField()


database.create_tables([Forecast])

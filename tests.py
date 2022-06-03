import datetime
import os
import unittest
from unittest.mock import Mock

import cv2

from base import database
from weather import DatabaseUpdater, Manager, ImageMaker
from weather_forecast import WeatherMaker


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with database.atomic():
            test_func(*args, **kwargs)
            database.rollback()

    return wrapper


class ForecastTest(unittest.TestCase):
    def setUp(self) -> None:
        self.predictor = WeatherMaker(res_holder=Mock(), lock=Mock(), day=datetime.date.today())
        self.db_updater = DatabaseUpdater()
        self.leader = Manager()
        self.painter = ImageMaker()

        self.ICONS_PATH = self.predictor.ICONS_PATH
        self.path_to_save_postcard = 'external_data/test_postcards'
        self.colours = ('32, 165, 218', '225, 105, 65', '235, 206, 135', '105, 105, 105')
        self.icon_files = ('sun.png', 'rain.png', 'snow.png', 'cloud.png')
        self.weather_types = ('Clear', 'Possible light rain', 'Light snow', 'Foggy')

        self.paths_to_icon = [os.path.normpath(os.path.join(self.ICONS_PATH, path)) for path in self.icon_files]
        self.icons = [cv2.imread(icon_path, -1) for icon_path in self.paths_to_icon]

    def test_connection(self):
        self.assertEqual(self.predictor.weather_resp.status_code, 200)

    def test_weather_type_handler(self):
        for i, weather_type in enumerate(self.weather_types):
            icon, colour = self.predictor._weather_type_handler(weather_type.lower())

            assert isinstance(icon, str), isinstance(colour, str)
            self.assertEqual(icon, self.paths_to_icon[i])
            self.assertEqual(colour, self.colours[i])

    @isolate_db
    def test_wrong_date(self):
        wrong_day = datetime.datetime.today() + datetime.timedelta(weeks=2)
        next_wrong_day = wrong_day + datetime.timedelta(days=1)
        self.leader.get_weather_data(wrong_day, next_wrong_day)
        self.db_updater.save_weather_to_db(self.leader.weather_data)
        res = self.db_updater.get_data_from_db(wrong_day, next_wrong_day)
        assert res[0][0] == 'No data', res[0][3] is None
        assert res[0][4] == (255, 255, 255)

    @isolate_db
    def test_database(self):
        test_date1, test_date2 = datetime.datetime(2021, 9, 28), datetime.datetime(2021, 9, 29)
        self.leader.get_weather_data(test_date1, test_date2)
        self.db_updater.insert_data(self.leader.weather_data)
        res = self.db_updater.get_data_from_db(test_date1, test_date2)
        self.assertEqual(len(res), (test_date2 - test_date1).days)

        for field in res:
            self.assertEqual(len(field), 5)
            assert isinstance(field[0], str), isinstance(field[1], datetime.date)
            assert isinstance(field[2], str), isinstance(field[3], str)
            assert isinstance(field[4], tuple)

    def test_postcard_generation(self):
        path_to_examples, examples = 'external_data/postcard_examples', ('14_oct.jpg', '16_oct.jpg',)
        data = [('Partly Cloudy', 'Thu, 14 Oct', '9', self.icons[3], (105, 105, 105)),
                ('Possible Light Rain', 'Sat, 16 Oct', '7', self.icons[1], (225, 105, 65))]
        for i, data_unit in enumerate(data):
            self.painter.draw_postcard(data_unit, self.path_to_save_postcard)
            example_postcard = os.path.normpath(os.path.join(path_to_examples, examples[i]))
            result_postcard = os.path.normpath(os.path.join(self.path_to_save_postcard, examples[i]))

            with open(example_postcard, 'rb') as example:
                with open(result_postcard, 'rb') as result:
                    example_content = example.read()
                    res_content = result.read()

            self.assertEqual(example_content, res_content)
            os.remove(result_postcard)

    @isolate_db
    def test_count_of_postcards(self):
        day1, day2 = '2021-10-15', '2021-10-16'
        date1, date2 = datetime.datetime.strptime(day1, '%Y-%m-%d'), datetime.datetime.strptime(day2, '%Y-%m-%d')

        count_of_postcards = len([name for name in os.listdir(self.path_to_save_postcard) if os.path.isfile(
            os.path.join(self.path_to_save_postcard, name))]) if os.path.exists(self.path_to_save_postcard) else 0

        Manager(f'-f {day1} -l {day2} -p', self.path_to_save_postcard).run()

        new_count = len([name for name in os.listdir(self.path_to_save_postcard) if os.path.isfile(
            os.path.join(self.path_to_save_postcard, name))]) if os.path.exists(self.path_to_save_postcard) else 0

        self.assertEqual((date2 - date1).days, new_count - count_of_postcards)
        [os.remove(os.path.join(self.path_to_save_postcard, name)) for name in os.listdir(self.path_to_save_postcard)]


if __name__ == '__main__':
    unittest.main()

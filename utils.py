import os

import cv2
from numpy import ndarray

from constants import ICON_FILE_NAME, ICONS_PATH, ICONS_DATA


def get_norm_and_join_path(*args: str) -> str:
    return os.path.normpath(os.path.join(*args))


def get_image(weather_type: str) -> ndarray:
    icon_name = ICONS_DATA[weather_type][ICON_FILE_NAME]
    path_to_icon = get_norm_and_join_path(ICONS_PATH, icon_name)
    return cv2.imread(path_to_icon, -1)


def viewImage(image, name_of_window):
    """Provide display postcard"""
    cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
    cv2.imshow(name_of_window, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def get_count_of_postcards(path: str) -> int:
    """Method returns count of files in path given. If path doesn't exist return 0

    :param path: directory to count files in"""
    if os.path.exists(path):
        return len([
            name for name in os.listdir(path) if os.path.isfile(
                os.path.join(path, name))])
    else:
        return 0


TEST_POSTCARDS_DATA = (
    (('Partly Cloudy', 'Thu, 14 Oct', '9', get_image('cloud'), (105, 105, 105)), '14_oct.jpg'),
    (('Possible Light Rain', 'Sat, 16 Oct', '7', get_image('rain'), (225, 105, 65)), '16_oct.jpg'),
)

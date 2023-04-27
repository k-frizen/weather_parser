import os

import cv2
from numpy import ndarray

from constants import ICON_FILE_NAME, ICONS_PATH, ICONS_DATA


def get_norm_and_joined_path(*args: str) -> str:
    """Get normalized and joined path.

    :param args: strings representing the paths to join
    :return: a normalized and joined path string
    """
    return os.path.normpath(os.path.join(*args))


def get_image(weather_type: str) -> ndarray:
    """Get image array of a weather type.

    :param weather_type: a string representing the type of weather
    :return: an array representing the weather icon image
    """
    icon_name = ICONS_DATA[weather_type][ICON_FILE_NAME]
    path_to_icon = get_norm_and_joined_path(ICONS_PATH, icon_name)
    return cv2.imread(path_to_icon, -1)


def viewImage(image, name_of_window):
    """Display an image.

    :param image: an image array to display
    :param name_of_window: a string representing the name of the display window
    """
    cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
    cv2.imshow(name_of_window, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def get_count_of_postcards(path: str) -> int:
    """Get the count of postcards in a directory.

    :param path: a string representing the directory to count postcards in
    :return: an integer representing the count of postcards in the directory, or 0 if the directory does not exist
    """
    if not os.path.exists(path):
        return 0

    files = set()
    for name in os.listdir(path):
        if os.path.isfile(os.path.join(path, name)):
            files.add(name)
    return len(files)


TEST_POSTCARDS_DATA = (
    (('Partly Cloudy', 'Thu, 14 Oct', '9', get_image('cloud'), (105, 105, 105)), '14_oct.jpg'),
    (('Possible Light Rain', 'Sat, 16 Oct', '7', get_image('rain'), (225, 105, 65)), '16_oct.jpg'),
)

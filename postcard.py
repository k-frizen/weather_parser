import os

import cv2
from numpy.core.multiarray import ndarray

from constants import *
from utils import viewImage, get_norm_and_joined_path


class ImageMaker:
    """"A class for creating weather postcards.

    This class provides methods for preparing data from a database and
    drawing weather information on a postcard template.
    """

    def __init__(self, path_to_save: str, path_to_template: str = TEMPLATE_PATH, ):
        """ Initializes an ImageMaker instance.

        Args:
            path_to_save (str): The directory where weather postcards will be stored.
            path_to_template (str): The path to the postcard's template file. Defaults to TEMPLATE_PATH.
        """
        self.__width, self.__height = 0, 0
        self.path_to_template = path_to_template
        self._font = cv2.FONT_HERSHEY_DUPLEX
        self.path_to_save = path_to_save

    def compare_background_and_icon(self, background: ndarray, icon: ndarray, colour: tuple) -> ndarray:
        """Overlays icon on postcard.

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

    def draw_postcard(self, data: tuple):
        """Draws picture with colored background, degrees, date and weather type caption.
        Displays result postcard and saves it.

        :param data: database field contains weather type and temp at this date, icon path and color to draw gradient
        """
        postcard_template = cv2.imread(self.path_to_template)
        weather_type, date, temp, icon, color = data

        postcard_side = max(postcard_template.shape[:2])
        resized_icon_shape = int(postcard_side * .4)

        postcard_background = cv2.resize(postcard_template, (postcard_side, postcard_side))

        self.__width, self.__height = postcard_background.shape[:2]
        background = postcard_background
        if icon is not None:
            resized_icon = cv2.resize(icon, (resized_icon_shape, resized_icon_shape))
            background = self.compare_background_and_icon(postcard_background, resized_icon, color)

        self.__place_text_on_image(background, weather_type, temp, date)
        viewImage(background, 'postcard')
        self.save_postcard(date, background)

    def __place_text_on_image(self, background: ndarray, weather_type: str, temp: str, date: str) -> None:
        """Adds text to the input background image, indicating the weather type, temperature, and date.

        Args:
            background (ndarray): The input background image as a NumPy array.
            weather_type (str): The type of weather, such as "sunny", "cloudy", or "rainy".
            temp (str): The temperature, in degrees Celsius, as a string.
            date (str): The date to display, in the format "weekday, day month", such as "Mon, 27 April".

        Returns:
            None. The input background image is modified in place."""
        x_coord_for_text = int(self.__width * .2) if len(weather_type) < 10 else int(self.__width * .1)
        common_params = dict(img=background, fontFace=self._font, fontScale=1, color=BLACK_COLOR, thickness=1)

        # write a weather type and temperature
        first_line_coord = x_coord_for_text, int(self.__height * .2)
        cv2.putText(text=f"{weather_type}, {temp} deg", org=first_line_coord, **common_params)

        # write a date in "weekday, day month" format
        second_line_coord = int(self.__width * .2), int(self.__height * .4)
        cv2.putText(text=date, org=second_line_coord, **common_params)

    def save_postcard(self, date: str, postcard: ndarray):
        """Save a postcard image to the given directory.

        :param date: the date in text format to be used in the filename
        :param postcard: the image of the postcard to be saved
        """
        file_name = "_".join(date.split()[1:]).lower()  # dd_mmm (01_jan, 30_oct, etc.)
        if not os.path.exists(self.path_to_save):
            os.makedirs(self.path_to_save)
        image_path = get_norm_and_joined_path(self.path_to_save, f'{file_name}.jpg')
        cv2.imwrite(image_path, postcard)

    def __draw_gradient(self, background: ndarray, color: tuple) -> None:
        """Draw a gradient on the given picture, from the given color to white.

        :param background: the image to draw the gradient on
        :param color: the starting color of the gradient"""
        color_shifts = [(255 - c) / self.__width for c in color]
        for indent in range(self.__width):
            cv2.line(background, (indent, 0), (indent, self.__height), color, 1)
            color = [rgb_value + shift for rgb_value, shift in zip(color, color_shifts)]  # next line color

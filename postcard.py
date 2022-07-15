import os

import cv2
from numpy.core.multiarray import ndarray


class ImageMaker:
    """The postcard Factory.

    This class prepares data from database to cover it postcard; draws a gradient on postcard;
    compares icon and postcard with gradient and text (date, temperature, weather)"""

    def __init__(self, path_to_template: str = 'external_data/template.jpg'):
        self.__width, self.__height = 0, 0
        self.path_to_template = path_to_template

    @staticmethod
    def viewImage(image, name_of_window):
        """Provide display postcard"""
        cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
        cv2.imshow(name_of_window, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

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

    def draw_postcard(self, data: tuple, path_to_save: str):
        """Draws picture with colored background, degrees, date and weather type caption.
        Displays result postcard and saves it.

        :param data: database field contains weather type and temp at this date, icon path and colour to draw gradient
        :param path_to_save: directory where weather postcards will be stored."""
        postcard_template = cv2.imread(self.path_to_template)
        weather_type, date, temp, icon, colour = data

        postcard_side = max(postcard_template.shape[:2])
        resized_icon_shape = int(postcard_side * .4)

        postcard_background = cv2.resize(postcard_template, (postcard_side, postcard_side))

        self.__width, self.__height = postcard_background.shape[:2]
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

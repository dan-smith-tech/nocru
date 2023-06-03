import numpy as np


class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


def get_minkowski_bounds(box, collider):
    """
    Gets the entire bounding area of a collider.

    :param box: a Rect for a new box that is being added to the image
    :param collider: a Rect for a collider currently on the image
    :return: a Rect for the bounding area of the collider
    """

    return Rect(collider.x - box.width,
                collider.y - box.height,
                collider.width + box.width,
                collider.height + box.height)


def get_image_bound_colliders(new_text_box, img_size):
    """
    Gets the boxes where a new text box's anchors cannot be placed.

    :param new_text_box: a Rect of the text to be placed in the image
    :param img_size: the resolution (height, width) of the image the text is being placed in
    :return: the Rects of the colliders
    """

    pass


def get_valid_bounds(existing_text_boxes, img_size):
    """
    Divide and conquer to find all boxes outside the colliders:
    https://stackoverflow.com/questions/60509252/how-do-i-get-the-rectangles-which-would-fill-out-a-space-excluding-some-other

    :param existing_text_boxes: a list of Rects of the existing text boxes
    :param img_size: the resolution (height, width) of the image the text is being placed in
    :return: a list of Rects of containing valid placement positions
    """

    pass


def get_text_position(new_text_box, existing_text_boxes, img_size):
    """
    Gets the position to place a text box in.

    :param new_text_box: a tuple containing (x, y, width, height) of the text to be placed in the image
    :param existing_text_boxes: a list of tuples containing (x, y, width, height) of the existing text boxes
    :param img_size: the resolution (height, width) of the image the text is being placed in
    :return: the position (y, x) of the text box
    """

    colliders = np.empty((len(existing_text_boxes) + 2))

    # get minkowski bounds for existing text boxes and image size store in colliders

    # divide and conquer to find all possible valid points

    # pick a random valid Rect, and a random position inside that Rect, and return


if __name__ == "__main__":
    get_text_position((56, 13, 100, 50), [], (1080, 1920))

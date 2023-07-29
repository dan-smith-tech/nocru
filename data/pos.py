import numpy as np
import copy


class TextBox(object):
    """
    Store position and content data of text to be placed on an image.
    """

    def __init__(self, x, y, width, height, text=None, font=None, color=None, stroke_width=None, stroke_color=None,
                 cutter_x=None, cutter_y=None, cutter_width=None, cutter_height=None, cutter_color=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = font
        self.color = color
        self.stroke_width = stroke_width
        self.stroke_color = stroke_color
        self.cutter_x = cutter_x
        self.cutter_y = cutter_y
        self.cutter_width = cutter_width
        self.cutter_height = cutter_height
        self.cutter_color = cutter_color


def get_minkowski_bounds(new_box, existing_box, img_size):
    """
    :param new_box: TextBox of the box to be added to the image
    :param existing_box: TextBox of a box currently in an image
    :param img_size: (width, height) of the image
    :return: TextBox of the collider including the bounding area
    """

    # if there is a cutter associated with the text box to be placed, adjust the bounds accordingly
    cutter_offset = 0
    if new_box.cutter_x is not None:
        cutter_offset = max((new_box.cutter_y + new_box.cutter_height) - (new_box.y + new_box.height), 0)

    # adjust position and size to account for bounds
    rect = copy.copy(existing_box)
    rect.x -= new_box.width
    rect.y -= new_box.height + cutter_offset
    rect.width += new_box.width
    rect.height += new_box.height + cutter_offset

    # if there is a cutter, minkowski it too
    if existing_box.cutter_x is not None:
        rect.cutter_x -= new_box.width
        rect.cutter_y -= new_box.height
        rect.cutter_width += new_box.width
        rect.cutter_height += new_box.height

    # clamp bounds
    if rect.x < 0:
        rect.width += rect.x
        rect.x = 0
    if rect.y < 0:
        rect.height += rect.y
        rect.y = 0
    rect.width = min(rect.width, img_size[0])
    rect.height = min(rect.height, img_size[1])

    return rect


def get_position(new_box, existing_boxes, img_size):
    """
    :param new_box: TextBox representing the new box to add
    :param existing_boxes: [TextBox] representing the existing boxes
    :param img_size: (width, height) of the image
    :return: (x, y) position to place the textbox on the image
    """

    # each point represents whether `new_box` can be placed there or not
    img = np.zeros((img_size[1], img_size[0]))

    boxes = copy.copy(existing_boxes)

    # pad image size
    boxes.append(TextBox(0, img_size[1], img_size[0], new_box.height))
    boxes.append(TextBox(img_size[0], 0, new_box.width, img_size[1]))

    for existing_box in boxes:
        collider = get_minkowski_bounds(new_box, existing_box, img_size)
        img[collider.y:collider.y + collider.height, collider.x:collider.x + collider.width] = 1

        # if there is a cutter associated with the current existing text box, remove the relevant points from options
        if collider.cutter_x is not None:
            img[collider.cutter_y:collider.cutter_y + collider.cutter_height,
                collider.cutter_x:collider.cutter_x + collider.cutter_width] = 1

    # find possible coordinates
    y, x = np.where(img == 0)

    # check if there are valid positions
    if len(x) == 0 or len(y) == 0:
        return -1, -1

    # select a random coordinate pair
    i = np.random.randint(len(x))
    return x[i], y[i]

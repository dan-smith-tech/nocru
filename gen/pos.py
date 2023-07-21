import numpy as np


class TextBox(object):
    def __init__(self, x, y, width, height, text, font, color, stroke_width, stroke_color, cutter_x=None, cutter_y=None,
                 cutter_width=None, cutter_height=None, cutter_color=None):
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
    :param new_box: TextBox representing the box to be added to the image
    :param existing_box: TextBox representing a box currently in an image
    :param img_size: (width, height) of the image
    :return: TextBox representing collider with a bounding area
    """

    rect = TextBox(existing_box.x - new_box.width,
                   existing_box.y - new_box.height,
                   existing_box.width + new_box.width,
                   existing_box.height + new_box.height,
                   existing_box.text, existing_box.font,
                   existing_box.color, existing_box.stroke_width, existing_box.stroke_color)

    if rect.x < 0:
        rect.width += rect.x
        rect.x = 0
    if rect.y < 0:
        rect.height += rect.y
        rect.y = 0
    if rect.width > img_size[0]:
        rect.width = img_size[0]
    if rect.height > img_size[1]:
        rect.height = img_size[1]

    return rect


def get_position(new_box, existing_boxes, img_size):
    """
    :param new_box: TextBox representing the new box to add
    :param existing_boxes: [TextBox] representing the existing boxes
    :param img_size: (width, height) of the image
    :return: (x, y) position to place the textbox on the image
    """

    img = np.zeros((img_size[1], img_size[0]))

    existing_boxes.append(TextBox(0, img_size[1], img_size[0], new_box.height, None, None, None, None, None))
    existing_boxes.append(TextBox(img_size[0], 0, new_box.width, img_size[1], None, None, None, None, None))
    for existing_box in existing_boxes:
        collider = get_minkowski_bounds(new_box, existing_box, img_size)
        img[collider.y:collider.y + collider.height, collider.x:collider.x + collider.width] = 1

    y, x = np.where(img == 0)

    if len(x) == 0 or len(y) == 0:
        return -1, -1

    i = np.random.randint(len(x))
    return [x[i], y[i]]

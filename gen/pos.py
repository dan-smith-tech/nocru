import numpy as np
import matplotlib.pyplot as plt


class TextBox(object):
    def __init__(self, x, y, width, height, text, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = font


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
                   existing_box.text, existing_box.font)

    if rect.x < 0:
        rect.width += rect.x
        rect.x = 0
    if rect.y < 0:
        rect.height += rect.y
        rect.y = 0
    # need to account for position offset:
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

    existing_boxes.append(TextBox(0, img_size[1], img_size[0], new_box.height, None, None))
    existing_boxes.append(TextBox(img_size[0], 0, new_box.width, img_size[1], None, None))
    for existing_box in existing_boxes:
        collider = get_minkowski_bounds(new_box, existing_box, img_size)
        img[collider.y:collider.y + collider.height, collider.x:collider.x + collider.width] = 1

    bx=existing_boxes[0]
    img[bx.y:bx.y + bx.height, bx.x:bx.x + bx.width] = 0.75

    img[new_box.y:new_box.y + new_box.height, new_box.x:new_box.x + new_box.width] = 0.5

    plt.imshow(img, cmap="gray")
    plt.show()

    x, y = np.where(img == 0)

    if len(x) == 0 or len(y) == 0:
        return -1, -1

    i = np.random.randint(len(x))
    return [x[i], y[i]]


def main():
    new_box = TextBox(30, 40, 20, 20, "hi", None)
    existing_box = TextBox(0, 0, 20, 30, "bi", None)
    print(get_position(new_box, [existing_box], (100, 100)))


if __name__ == "__main__":
    main()
    # img = np.zeros((5, 5))
    # x = 3
    # y = 0
    # w = 2
    # h = 3
    # img[y:y + h, x:x + w] = 1
    # print(img)

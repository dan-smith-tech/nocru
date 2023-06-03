import numpy as np
import random
from collections import namedtuple


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
    # overlap may occur after minkowski. CAUSES ISSUES IN DIVCONQ

    # divide and conquer to find all possible valid points

    # pick a random valid Rect, and a random position inside that Rect, and return
    # !! dont forget to check for edgecase where no valid positions exist. dont forget to add l and t values to resultant anchor point before return in order to convert from absolute anchor to pillow anchor


# div and conq crap
# conversion like so:
# x1 = x
# y1 = y
# x2 = x + width
# y2 = y + height
# Rectangle = Rect

# !! must fix for overlap possibility !! either here or in minkowski (probably here)

def intersects(b, r):
    return b.x < r.x + r.width and b.x + b.width > r.x and b.y < r.y + r.height and b.y + b.height > r.y

# custom min thing to adujust for relative anchor and not absolute
def custom_minW(b, r):
    if (min(b.x + b.width, r.x + r.width) == b.x + b.width):
        return b.width
    else:
        return r.width
    
def custom_minH(b, r):
    if (min(b.x + b.height, r.x + r.height) == b.x + b.height):
        return b.height
    else:
        return r.height

def clip_rect(b, r):
    return Rect(
        max(b.x, r.x), max(b.y, r.y),
        custom_minW(b, r), custom_minH(b, r)
    )

def clip_rects(b, rects):
    return [clip_rect(b, r) for r in rects if intersects(b, r)]

# entrypoint
def split_rectangles(b, rects):
    if b.x >= b.x + b.width or b.y >= b.y + b.height:
        pass
    elif not rects:
        yield b
    else:
        # randomize to avoid O(n^2) runtime in typical cases
        # change this if deterministic behaviour is required
        pivot = random.choice(rects)

        above = Rect(b.x,     b.y,     b.x + b.width,     pivot.y)
        left  = Rect(b.x,     pivot.y, pivot.x, pivot.height)
        right = Rect(pivot.x + pivot.width, pivot.y, b.width - (pivot.x + pivot.width),     pivot.height)
        below = Rect(b.x,     pivot.y + pivot.height, b.x + b.width,     b.height - (pivot.y + pivot.height))

        yield from split_rectangles(above, clip_rects(above, rects))
        yield from split_rectangles(left,  clip_rects(left,  rects))
        yield from split_rectangles(right, clip_rects(right, rects))
        yield from split_rectangles(below, clip_rects(below, rects))


if __name__ == "__main__":
    # get_text_position((56, 13, 100, 50), [], (1080, 1920))
    existing = [Rect(100, 200, 300, 400), Rect(400, 200, 700, 200)]
    bounding = Rect(0, 0, 1920, 1080)
    for things in split_rectangles(bounding, existing):
        print(things.x, things.y, things.width, things.height)
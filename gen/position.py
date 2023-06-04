import numpy as np
import random
from PIL import Image, ImageDraw
from collections import namedtuple
import sys

Rectangle = namedtuple('Rectangle', 'x1 y1 x2 y2')

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


def get_collision_bounds(new_text_box, existing_text_boxes, img_size):
    colliders = []

    # get minkowski bounds for existing text boxes and image size store in colliders
    # overlap may occur after minkowski. CAUSES ISSUES IN DIVCONQ
    # no anchor conversion needed, pillow now set to use topleft anchor. is only ever a couple of pixels out on the x axis, negligible therefore ignoring
    for box in existing_text_boxes:
        colliders.append(get_minkowski_bounds(new_text_box, box))
    # add rightmost and bottommost minkowski bounds
    # colliders.append(Rect(img_size.width - new_text_box.width, 0, new_text_box.width, img_size.height))
    # colliders.append(Rect(0, img_size.height - new_text_box.height, img_size.width,
    #                       new_text_box.height))

    return colliders


def intersects(b, r):
    return b.x1 < r.x2 and b.x2 > r.x1 and b.y1 < r.y2 and b.y2 > r.y1

def clip_rect(b, r):
    return Rectangle(
        max(b.x1, r.x1), max(b.y1, r.y1),
        min(b.x2, r.x2), min(b.y2, r.y2)
    )

def clip_rects(b, rects):
    return [clip_rect(b, r) for r in rects if intersects(b, r)]

def split_rectangles(b, rects):
    if b.x1 >= b.x2 or b.y1 >= b.y2:
        pass
    elif not rects:
        yield b
    else:
        # randomize to avoid O(n^2) runtime in typical cases
        # change this if deterministic behaviour is required
        pivot = random.choice(rects)

        above = Rectangle(b.x1,     b.y1,     b.x2,     pivot.y1)
        left  = Rectangle(b.x1,     pivot.y1, pivot.x1, pivot.y2)
        right = Rectangle(pivot.x2, pivot.y1, b.x2,     pivot.y2)
        below = Rectangle(b.x1,     pivot.y2, b.x2,     b.y2)

        yield from split_rectangles(above, clip_rects(above, rects))
        yield from split_rectangles(left,  clip_rects(left,  rects))
        yield from split_rectangles(right, clip_rects(right, rects))
        yield from split_rectangles(below, clip_rects(below, rects))


# def intersects(b, r):
#     return b.x < (r.x + r.width) and (b.x + b.width) > r.x and b.y < (r.y + r.height) and (b.y + b.height) > r.y


# # custom min thing to adjust for relative anchor and not absolute
# def custom_minW(b, r):
#     if (min(b.x + b.width, r.x + r.width) == b.x + b.width):
#         return b.width
#     else:
#         return r.width


# def custom_minH(b, r):
#     if (min(b.y + b.height, r.y + r.height) == b.y + b.height):
#         return b.height
#     else:
#         return r.height


# def clip_rect(b, r):
#     return Rect(
#         max(b.x, r.x), max(b.y, r.y),
#         # custom_minW(b, r), custom_minH(b, r)
#         min((b.x + b.width), (r.x + r.width)), min((b.y + b.height), (r.y + r.height))
#     )


# def clip_rects(b, rects):
#     return [clip_rect(b, r) for r in rects if intersects(b, r)]


# def get_valid_bounds(rects, b):
#     if b.x >= (b.x + b.width) or b.y >= (b.y + b.height):
#         pass
#         print("TRIGGER")
#     elif not rects:
#         yield b
#     else:
#         # randomize to avoid O(n^2) runtime in typical cases
#         # change this if deterministic behaviour is required
#         pivot = random.choice(rects)
#         # print("pivot is " + str(pivot.x), str(pivot.y), str(pivot.width), str(pivot.height))
#         # print("b is " + str(b.x), str(b.y), str(b.width), str(b.height))

#         above = Rect(b.x, b.y, b.x + b.width, pivot.y)
#         left = Rect(b.x, pivot.y, pivot.x, pivot.y + pivot.height)
#         right = Rect(pivot.x + pivot.width, pivot.y, b.x + b.width, pivot.y + pivot.height)
#         below = Rect(b.x, pivot.y + pivot.height, b.x + b.width, b.y + b.height)

#         yield from get_valid_bounds(clip_rects(above, rects), above)
#         yield from get_valid_bounds(clip_rects(left, rects), left)
#         yield from get_valid_bounds(clip_rects(right, rects), right)
#         yield from get_valid_bounds(clip_rects(below, rects), below)


def draw_boxes(sections, colliders, img_size, new_text_box=None):
    img = Image.new("RGB", img_size)
    # only need to call draw once
    new_img = ImageDraw.Draw(img)
    new_img.rectangle([0, 0, img_size[0], img_size[1]], fill="white", width=0)

    for section in sections:
        new_img.rectangle(((section.x, section.y), (section.x + section.width, section.y + section.height)),
                          fill="green", outline="black", width=1)

    for collider in colliders:
        print(collider.x, collider.y, collider.width, collider.height)
        new_img.rectangle(((collider.x, collider.y), (collider.x + collider.width, collider.y + collider.height)),
                          fill="red")

    if new_text_box:
        new_img.rectangle(((new_text_box.x, new_text_box.y),
                           (new_text_box.x + new_text_box.width, new_text_box.y + new_text_box.height)), fill="blue")

    img.show()


def get_text_position(new_text_box_size, existing_text_boxes_pos, img_size, draw=False):
    """
    Gets the position to place a text box in.

    :param new_text_box_pos: a tuple containing (x, y, width, height) of the text to be placed in the image
    :param existing_text_boxes_pos: a list of tuples containing (x, y, width, height) of the existing text boxes
    :param img_size: the resolution (width, height) of the image the text is being placed in
    :param draw: shows the box placement as an image
    :return: the position (y, x) of the text box
    """

    new_text_box = Rect(0, 0, new_text_box_size[0], new_text_box_size[1])
    # existing_text_boxes = [Rect(box[0], box[1], box[2], box[3]) for box in existing_text_boxes_pos]
    existing_text_boxes = existing_text_boxes_pos
    img_bounds = Rect(0, 0, img_size[0], img_size[1])

    colliders = get_collision_bounds(new_text_box, existing_text_boxes, img_bounds)

    for c in colliders:
        print(c.x, c.y, c.width, c.height)
    print(img_bounds.x, img_bounds.y, img_bounds.width, img_bounds.height, end="\n----------------\n")

    # for thing in get_valid_bounds(colliders, img_bounds):
    #     print(thing.x, thing.y, thing.width, thing.height)

    # valid_rects = list(get_valid_bounds(colliders, img_bounds))
    colliders1 = []
    for col in colliders:
        colliders1.append(Rectangle(col.x, col.y, col.x + col.width, col.y + col.height))
    valid_rects1 = list(split_rectangles(Rectangle(img_bounds.x, img_bounds.y, img_bounds.width, img_bounds.height), colliders1))

    valid_rects = []
    for val in valid_rects1:
        valid_rects.append(Rect(val.x1, val.y1, val.x2 - val.x1, val.y2 - val.y1))

    if len(valid_rects) > 0:
        chosen = random.choice(valid_rects)
        new_text_box.x = np.random.randint(chosen.x, (chosen.x + chosen.width) + 1)
        new_text_box.y = np.random.randint(chosen.y, (chosen.y + chosen.height) + 1)

        # dont forget to draw the original boxes, not the colliders, since colliders are minkowski'd
        if draw:
            draw_boxes(valid_rects, existing_text_boxes, img_size, new_text_box=new_text_box)
    elif draw:
        draw_boxes(valid_rects, existing_text_boxes, img_size)
        print("no valid positions found")


if __name__ == "__main__":
    existing = [
        Rect(60, 150, 350, 450),
        Rect(700, 700, 50, 50),
        Rect(0, 1030, 1920, 50)
    ]
    bounding = Rect(0, 0, 1920, 1080)

    for e in existing:
        print(e.x, e.y, e.width, e.height)
    print(bounding.x, bounding.y, bounding.width, bounding.height, end="\n----------------\n")

    # for things in get_valid_bounds(existing, bounding):
    #     print(things.x, things.y, things.width, things.height)

    print("\ncompared to...\n")
    get_text_position((50, 50), existing, (bounding.width, bounding.height), draw=True)
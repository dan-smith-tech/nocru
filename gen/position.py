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


def get_minkowski_bounds(box, collider, img_size):
    """
    Gets the entire bounding area of a collider.

    :param box: a Rect for a new box that is being added to the image
    :param collider: a Rect for a collider currently on the image
    :return: a Rect for the bounding area of the collider
    """

    rect = Rect(collider.x - box.width,
                collider.y - box.height,
                collider.width + box.width,
                collider.height + box.height)

    if rect.x < 0:
        rect.x = 0
    if rect.y < 0:
        rect.y = 0
    if rect.width > img_size.width:
        rect.width = img_size.width
    if rect.height > img_size.height:
        rect.height = img_size.width

    return rect


def get_collision_bounds(new_text_box, existing_text_boxes, img_size):
    colliders = []

    # get minkowski bounds for existing text boxes and image size store in colliders
    # overlap may occur after minkowski. CAUSES ISSUES IN DIVCONQ
    # no anchor conversion needed, pillow now set to use topleft anchor. is only ever a couple of pixels out on the x axis, negligible therefore ignoring
    for box in existing_text_boxes:
        colliders.append(get_minkowski_bounds(new_text_box, box, img_size))
    # add rightmost and bottommost minkowski bounds
    colliders.append(Rect(img_size.width - new_text_box.width, 0, new_text_box.width, img_size.height))
    colliders.append(Rect(0, img_size.height - new_text_box.height, img_size.width,
                          new_text_box.height))
    
    # overlap fixer
    # yes i put it here even though it totally should be a different method
    colliders1 = convert_to_absolute(colliders)
    for col1 in colliders1:
        for col2 in colliders1:
            if (col1 != col2):
                if (intersects(col1, col2)):
                    # is completely enclosed
                    if (col1.x1 > col2.x1 and col1.x2 < col2.x2 and col1.y1 > col2.y1 and col1.y2 < col2.y2):
                        print("trigger enclosed")
                        colliders1.remove(col1)
                    # side-overlap right
                    elif (col2.x1 <= col1.x1 <= col2.x2 and col1.x2 > col2.x2):
                        print("trigger right")
                        new = Rectangle(col2.x2, col1.y1, col1.x2, col1.y2)
                        # corner overlaps right
                        if (col1.y1 < col2.y1):
                            print("trigger right top")
                            new2 = Rectangle(col1.x1, col1.y1, col2.x2, col2.y1)
                            colliders1.append(new2)
                        elif (col1.y2 > col2.y2):
                            print("trigger right bottom")
                            new2 = Rectangle(col1.x1, col2.y2, col2.x2, col1.y2)
                            colliders1.append(new2)
                        colliders1.remove(col1)
                        colliders1.append(new)
                    # side-overlap left
                    elif (col2.x1 < col1.x2 < col2.x2 and col1.x1 < col2.x1):
                        print("trigger left")
                        new = Rectangle(col1.x1, col1.y1, col2.x1, col1.y2)
                        # corner overlaps left
                        if (col1.y1 < col2.y1):
                            print("trigger left top")
                            new2 = Rectangle(col2.x1, col1.y1, col1.x2, col2.y1)
                            colliders1.append(new2)
                        elif (col1.y2 > col2.y2):
                            print("trigger left bottom")
                            new2 = Rectangle(col2.x1, col2.y2, col1.x2, col1.y2)
                            colliders1.append(new2)
                        colliders1.remove(col1)
                        colliders1.append(new)
                    # +-type overlap
                    elif (col1.x1 < col2.x1 and col1.x2 > col2.x2 and col1.y1 > col2.y1 and col1.y2 < col2.y2):
                        print("trigger +")
                        new0 = Rectangle(col1.x1, col1.y1, col2.x1, col1.y2)
                        new1 = Rectangle(col2.x2, col1.y1, col1.x2, col1.y2)
                        colliders1.remove(col1)
                        colliders1.append(new0)
                        colliders1.append(new1)
                    # top overlap
                    elif (col1.x1 >= col2.x1 and col1.x2 <= col2.x2 and col1.y1 <= col2.y1 and col1.y2 >= col2.y1):
                        print("trigger top")
                        new = Rectangle(col1.x1, col1.y1, col1.x2, col2.y1)
                        colliders1.remove(col1)
                        colliders1.append(new)
                    # bottom overlap
                    elif (col1.x1 >= col2.x1 and col1.x2 <= col2.x2 and col1.y1 >= col2.y1 and col1.y2 >= col2.y2):
                        print("trigger bottom")
                        new = Rectangle(col1.x1, col2.y2, col1.x2, col1.y2)
                        colliders1.remove(col1)
                        colliders1.append(new)
                    else:
                        print("!!!unaccounted overlap, might cause issues!!!")
                        print("col1 = " + str(col1.x1) + " " + str(col1.y1) + " " + str(col1.x2) + " " + str(col1.y2))
                        print("col2 = " + str(col2.x1) + " " + str(col2.y1) + " " + str(col2.x2) + " " + str(col2.y2))
    colliders2 = convert_to_relative(colliders1)
    return colliders2


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

def convert_to_absolute(rects):
    rects1 = []
    for col in rects:
        rects1.append(Rectangle(col.x, col.y, col.x + col.width, col.y + col.height))
    return rects1

def convert_to_relative(rects):
    rects1 = []
    for val in rects:
        rects1.append(Rect(val.x1, val.y1, val.x2 - val.x1, val.y2 - val.y1))
    return rects1

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
    existing_text_boxes = existing_text_boxes_pos
    img_bounds = Rect(0, 0, img_size[0], img_size[1])

    colliders = get_collision_bounds(new_text_box, existing_text_boxes, img_bounds)

    for c in colliders:
        print(c.x, c.y, c.width, c.height)
    print(img_bounds.x, img_bounds.y, img_bounds.width, img_bounds.height, end="\n----------------\n")

    colliders1 = convert_to_absolute(colliders)
    valid_rects1 = list(split_rectangles(Rectangle(img_bounds.x, img_bounds.y, img_bounds.width, img_bounds.height), colliders1))

    valid_rects = convert_to_relative(valid_rects1)

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
import numpy as np
import random
from PIL import Image, ImageDraw


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
    for i, box in enumerate(existing_text_boxes):
        colliders.append(get_minkowski_bounds(new_text_box, box))
    # add rightmost and bottommost minkowski bounds
    colliders.append(Rect(img_size.width - new_text_box.width, 0, new_text_box.width, img_size.height))
    colliders.append(Rect(0, img_size.height - new_text_box.height, img_size.width,
                          new_text_box.height))

    return colliders


def intersects(b, r):
    return b.x < r.x + r.width and b.x + b.width > r.x and b.y < r.y + r.height and b.y + b.height > r.y


# custom min thing to adjust for relative anchor and not absolute
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


def get_valid_bounds(rects, b):
    if b.x >= b.x + b.width or b.y >= b.y + b.height:
        pass
    elif not rects:
        yield b
    else:
        # randomize to avoid O(n^2) runtime in typical cases
        # change this if deterministic behaviour is required
        pivot = random.choice(rects)

        above = Rect(b.x, b.y, b.x + b.width, pivot.y)
        left = Rect(b.x, pivot.y, pivot.x, pivot.height)
        right = Rect(pivot.x + pivot.width, pivot.y, b.width - (pivot.x + pivot.width), pivot.height)
        below = Rect(b.x, pivot.y + pivot.height, b.x + b.width, b.height - (pivot.y + pivot.height))

        yield from get_valid_bounds(clip_rects(above, rects), above)
        yield from get_valid_bounds(clip_rects(left, rects), left)
        yield from get_valid_bounds(clip_rects(right, rects), right)
        yield from get_valid_bounds(clip_rects(below, rects), below)


def draw_boxes(sections, colliders, img_size, new_text_box=None):
    img = Image.new("RGB", img_size)

    for section in sections:
        new_img = ImageDraw.Draw(img)
        new_img.rectangle(((section.x, section.y), (section.x + section.width, section.y + section.height)),
                          fill="white", outline="yellow", width=3)

    for collider in colliders:
        new_img = ImageDraw.Draw(img)
        new_img.rectangle(((collider.x, collider.y), (collider.x + collider.width, collider.y + collider.height)),
                          fill="black")

    if new_text_box:
        new_img = ImageDraw.Draw(img)
        new_img.rectangle(((new_text_box.x, new_text_box.y),
                           (new_text_box.x + new_text_box.width, new_text_box.y + new_text_box.height)), fill="blue")

    img.show()


def get_text_position(new_text_box_pos, existing_text_boxes_pos, img_size, draw=False):
    """
    Gets the position to place a text box in.

    :param new_text_box_pos: a tuple containing (x, y, width, height) of the text to be placed in the image
    :param existing_text_boxes_pos: a list of tuples containing (x, y, width, height) of the existing text boxes
    :param img_size: the resolution (width, height) of the image the text is being placed in
    :param draw: shows the box placement as an image
    :return: the position (y, x) of the text box
    """

    new_text_box = Rect(-1, -1, new_text_box_pos[0], new_text_box_pos[1])
    existing_text_boxes = [Rect(box[0], box[1], box[2], box[3]) for box in existing_text_boxes_pos]
    img_bounds = Rect(0, 0, img_size[0], img_size[1])

    colliders = get_collision_bounds(new_text_box, existing_text_boxes, img_bounds)

    for c in colliders:
        print(c.x, c.y, c.width, c.height)
    print(img_bounds.x, img_bounds.y, img_bounds.width, img_bounds.height, end="\n----------------\n")

    for thing in get_valid_bounds(colliders, img_bounds):
        print(thing.x, thing.y, thing.width, thing.height)

    valid_rects = list(get_valid_bounds([colliders[2]], img_bounds))

    if len(valid_rects) > 0:
        chosen = random.choice(valid_rects)
        new_text_box.x = np.random.randint(chosen.x, (chosen.x + chosen.width) + 1)
        new_text_box.y = np.random.randint(chosen.y, (chosen.y + chosen.height) + 1)

        if draw:
            draw_boxes(valid_rects, colliders, img_size, new_text_box=new_text_box)
    elif draw:
        draw_boxes(valid_rects, colliders, img_size)


if __name__ == "__main__":
    existing = [
        Rect(50, 150, 350, 450),
        Rect(1870, 0, 50, 1080),
        Rect(0, 1030, 1920, 50),
    ]
    bounding = Rect(0, 0, 1920, 1080)

    for e in existing:
        print(e.x, e.y, e.width, e.height)
    print(bounding.x, bounding.y, bounding.width, bounding.height, end="\n----------------\n")

    for things in get_valid_bounds(existing, bounding):
        print(things.x, things.y, things.width, things.height)

    print("\ncompared to...\n")

    get_text_position((50, 50), [(100, 200, 300, 400)], (1920, 1080), draw=True)

from essential_generators import DocumentGenerator
from perlin_numpy import generate_perlin_noise_2d
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import re
import os

from data.pos import get_position
from data.pos import TextBox


def get_sentence():
    """
    Randomly generates a nonsense sentence.

    :return: String of the random sentence
    """

    gen = DocumentGenerator()

    sentence = gen.sentence()
    sentence = sentence.replace("–", "-").replace("—", "-").replace("—", "-")
    sentence = re.sub("[\s]+", " ", sentence)
    sentence = re.sub("[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]", "", sentence)

    return sentence


def get_text(draw, img_size):
    """
    Randomly selects a font from the 'data/fonts' directory.

    :param draw: ImageDraw (mutated) that holds the current state of the image being generated
    :param img_size: (width, height) of the image
    :return: ImageFont.FreeTypeFont of the selected font
    """

    sentence = get_sentence()

    # load a random local font
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(current_dir, "./fonts/")
    font = ImageFont.FreeTypeFont(font_dir + random.choice(os.listdir(font_dir)), np.random.randint(50, 100))

    if (draw.textbbox((0, 0), sentence, font=font, anchor="la")[2] > img_size[0] or
            draw.textbbox((0, 0), sentence, font=font, anchor="la")[3] > img_size[1]):
        return get_text(draw, img_size)

    return font, sentence


def create_textbox(existing_boxes, draw, img_size):
    """
    Generates a TextBox to be placed on an image.

    :param existing_boxes: [TextBox] of the current boxes placed on the image
    :param draw: ImageDraw (mutated) that holds the current state of the image being generated
    :param img_size: (width, height) of the image
    :return: TextBox of the new text placed on the image
    """

    font, sentence = get_text(draw, img_size)

    left, top, width, height = draw.textbbox((0, 0), sentence, font=font, anchor="la")

    color, stroke_color = random.sample([0, 255], 2)
    stroke_width = random.choice([2, 6])
    new_box = TextBox(0, 0, width, height, sentence, font, color, stroke_width, stroke_color)

    # 50% chance to add an overlap box
    if np.random.randint(0, 2):
        cutter_height = np.random.randint(round(new_box.height * 0.15), round(new_box.height * 0.3))
        cutter_offset = np.random.randint(round(new_box.height * 0.1), round(new_box.height * 0.2))

        new_box.cutter_x = new_box.x
        new_box.cutter_y = new_box.y + new_box.height - cutter_offset
        new_box.cutter_width = new_box.width
        new_box.cutter_height = cutter_height
        new_box.cutter_color = random.choice([0, 255])

    x_pos, y_pos = get_position(new_box, existing_boxes, (img_size[0], img_size[1]))
    new_box.x = x_pos
    new_box.y = y_pos

    if new_box.cutter_x is not None:
        new_box.cutter_x += new_box.x
        new_box.cutter_y += new_box.y

    return new_box


def generate_image():
    """
    Generates a random image containing random text and a perlin noise backdrop, labelled.

    :return: (Image, [TextBox]) of the generated image and respective label
    """

    # hardcoded image properties that match scaling of other features (e.g., font size)
    img_size = (1920, 1080)
    noise_scale = (27, 48)

    noise = (generate_perlin_noise_2d((img_size[1], img_size[0]), noise_scale) * 255).astype(np.uint8)
    img = Image.fromarray(noise)
    draw = ImageDraw.Draw(img)
    text_boxes = []

    for i in range(random.randrange(8)):
        new_box = create_textbox(text_boxes, draw, img_size)

        # if the text fits on the image somewhere, place it
        if new_box.x > -1 and new_box.y > -1:
            draw.text((new_box.x, new_box.y), new_box.text, font=new_box.font, fill=new_box.color,
                      stroke_width=new_box.stroke_width, stroke_fill=new_box.stroke_color)
            # change FreeTypeFont to (name, weight) of font
            new_box.font = new_box.font.getname()

            # if there is a cutter associated with this text box, place it
            if new_box.cutter_x:
                draw.rectangle((new_box.cutter_x, new_box.cutter_y, new_box.cutter_x + new_box.cutter_width,
                                new_box.cutter_y + new_box.cutter_height),
                               fill=new_box.cutter_color, outline=None, width=1)
            text_boxes.append(new_box)

    return img, text_boxes

from essential_generators import DocumentGenerator
from perlin_numpy import generate_perlin_noise_2d
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import json
import re
import os

from pos import get_position
from pos import TextBox


class NpTypeEncoder(json.JSONEncoder):
    """
    Encoder override to convert numpy types to standard Python types for JSON serialization.
    """

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpTypeEncoder, self).default(obj)


def get_sentence():
    """
    Randomly generates a nonsense sentence.

    :return: String of the random sentence
    """

    gen = DocumentGenerator()

    sentence = gen.sentence()
    sentence = sentence.replace("–", "-").replace("—", "-").replace("—", "-").replace("'", "")
    sentence = re.sub("[\s]+", " ", sentence)
    sentence = re.sub("[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]", "", sentence)

    return sentence


def get_font(sentence, draw, img_size):
    """
    Randomly selects a font from the 'gen/fonts' directory.

    :param sentence: String representing the sentence to be displayed
    :param draw: ImageDraw (mutated) that holds the current state of the image being generated
    :param img_size: (width, height) of the image
    :return: ImageFont.FreeTypeFont of the selected font
    """

    font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100))

    # makes sure sentence isnt literally too wide for the image. retries if it is.
    while (draw.textbbox((0, 0), sentence, font=font, anchor="lt")[2] > img_size[0] or
           draw.textbbox((0, 0), sentence, font=font, anchor="lt")[3] > img_size[1]):
        font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100))

    return font


def create_textbox(existing_boxes, draw, img_size):
    """
    Generates a TextBox to be placed on an image.

    :param existing_boxes: [TextBox] of the current boxes placed on the image
    :param draw: ImageDraw (mutated) that holds the current state of the image being generated
    :param img_size: (width, height) of the image
    :return: TextBox of the new text placed on the image
    """

    sentence = get_sentence()
    font = get_font(sentence, draw, img_size)

    left, top, width, height = draw.textbbox((0, 0), sentence, font=font, anchor="lt")
    color, stroke_color = random.sample([0, 255], 2)
    stroke_width = random.choice([2, 6])
    new_box = TextBox(0, 0, width, height, sentence, font, color, stroke_width, stroke_color)

    x_pos, y_pos = get_position(new_box, existing_boxes, (img_size[0], img_size[1]))
    new_box.x = x_pos
    new_box.y = y_pos

    # 50% chance to add an overlap box
    if np.random.randint(0, 2):
        new_box.cutter_x = new_box.x
        new_box.cutter_y = new_box.y + new_box.height - np.random.randint(0, 5)
        new_box.cutter_width = new_box.width
        new_box.cutter_height = np.random.randint(10, 50)
        new_box.cutter_color = random.choice([0, 255])

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


def generate_dataset(size, start=0, directory="../dataset/"):
    """
    :param size: Integer quantity of images to generate
    :param start: Integer index to begin generating at
    :param directory: String of relative location to save images to (including trailing slash)
    """

    for i in range(start, start + size):
        new_image, text_boxes = generate_image()
        new_image.save(directory + str(i) + ".png")

        label = {
            "id": i,
            "text_boxes": [box.__dict__ for box in text_boxes]
        }

        with open(directory + str(i) + '.json', 'w', encoding='utf-8') as f:
            json.dump(label, f, cls=NpTypeEncoder, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    size = int(input("Size of dataset: "))
    start = int(input("Start index: "))
    print("Dataset generating...")
    generate_dataset(size, start=start)
    print("Dataset completed.")

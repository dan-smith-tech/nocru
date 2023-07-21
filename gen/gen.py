from perlin_numpy import generate_perlin_noise_2d
from essential_generators import DocumentGenerator
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import json
import re
import os

from pos import TextBox
from pos import get_position


class NpTypeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpTypeEncoder, self).default(obj)


def get_sentence():
    gen = DocumentGenerator()

    sentence = gen.sentence()
    sentence = sentence.replace("–", "-").replace("—", "-").replace("—", "-").replace("'", "")
    sentence = re.sub("[\s]+", " ", sentence)
    sentence = re.sub("[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]", "", sentence)

    return sentence


def generate_image(img_size, noise_scale=(27, 48)):
    """
    :param img_size: (width, height) of the image
    :param noise_scale: scale of perlin noise pattern (smaller is more zoomed in, must be multiples of respective axes)
    :return: the generated image
    """

    noise = (generate_perlin_noise_2d((img_size[1], img_size[0]), noise_scale) * 255).astype(np.uint8)
    img = Image.fromarray(noise)
    draw = ImageDraw.Draw(img)
    boxes = []
    text_boxes = []

    num_sentences = np.random.randint(1, 8)
    cur_sentences = 0
    while cur_sentences < num_sentences:
        sentence = get_sentence()
        font = ImageFont.FreeTypeFont(
            "fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100)
        )
        while (draw.textbbox((0, 0), sentence, font=font, anchor="lt")[2] > img_size[0] or
               draw.textbbox((0, 0), sentence, font=font, anchor="lt")[3] > img_size[1]):
            font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100))

        left, top, width, height = draw.textbbox((0, 0), sentence, font=font, anchor="lt")
        color, stroke_color = random.sample([0, 255], 2)
        stroke_width = random.choice([2, 6])
        new_box = TextBox(0, 0, width, height, sentence, font, color, stroke_width, stroke_color)

        x_pos, y_pos = get_position(new_box, boxes, (img_size[0], img_size[1]))
        new_box.x = x_pos
        new_box.y = y_pos

        if x_pos > -1 and y_pos > -1:
            draw.text(
                (x_pos, y_pos),
                new_box.text,
                font=new_box.font,
                fill=new_box.color,
                stroke_width=new_box.stroke_width,
                stroke_fill=new_box.stroke_color,
            )
            if np.random.randint(0, 2):
                offset = np.random.randint(0, 20)
                cutter = TextBox(new_box.x - offset, (new_box.y + new_box.height) - np.random.randint(0, 5),
                                 new_box.width + offset + np.random.randint(0, 20), np.random.randint(10, 50),
                                 None, None, random.choice([0, 255]), 0, None)
                draw.rectangle((cutter.x, cutter.y, cutter.x + cutter.width, cutter.y + cutter.height),
                               fill=cutter.color, outline=None, width=1)
                boxes.append(cutter)
                new_box.cutter_x = cutter.x
                new_box.cutter_y = cutter.y
                new_box.cutter_width = cutter.width
                new_box.cutter_height = cutter.height
                new_box.cutter_color = cutter.color
            boxes.append(new_box)
            new_box.font = new_box.font.getname()
            text_boxes.append(new_box)

        cur_sentences += 1

    return img, text_boxes


def generate_dataset(num_images, directory, img_size):
    """
    :param num_images: Integer quantity of images to generate
    :param directory: relative location to save images in (include trailing slash)
    :param img_size: (width, height) of the image
    :return: None
    """

    for i in range(num_images):
        new_image, text_boxes = generate_image(img_size)
        new_image.save(directory + str(i) + ".png")

        label = {
            "id": i,
            "text_boxes": [box.__dict__ for box in text_boxes]
        }

        with open(directory + str(i) + '.json', 'w', encoding='utf-8') as f:
            json.dump(label, f, cls=NpTypeEncoder, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    generate_dataset(1, "../out/", (1920, 1080))

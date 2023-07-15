from perlin_numpy import generate_perlin_noise_2d
from essential_generators import DocumentGenerator
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import csv
import re
import os

from pos import TextBox
from pos import get_position


def get_sentence():
    gen = DocumentGenerator()

    sentence = gen.sentence()
    sentence = sentence.replace("–", "-").replace("—", "-").replace("—", "-")
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
        new_box = TextBox(0, 0, width, height, sentence, font)

        x_pos, y_pos = get_position(new_box, boxes, (img_size[0], img_size[1]))
        new_box.x = x_pos
        new_box.y = y_pos

        if x_pos > -1 and y_pos > -1:
            fill, stroke = random.sample([0, 255], 2)
            draw.text(
                (x_pos, y_pos),
                new_box.text,
                font=new_box.font,
                fill=fill,
                stroke_width=random.choice([2, 6]),
                stroke_fill=stroke,
            )
            if np.random.randint(0, 2):
                offset = np.random.randint(0, 20)
                cutter = TextBox(new_box.x - offset, (new_box.y + new_box.height) - np.random.randint(0, 5),
                                 new_box.width + offset + np.random.randint(0, 20), np.random.randint(10, 50),
                                 new_box.font, "if you're seeing this, something has gone terribly wrong.")
                draw.rectangle((cutter.x, cutter.y, cutter.x + cutter.width, cutter.y + cutter.height),
                               fill=random.choice(["black", "white"]), outline=None, width=1)
                boxes.append(cutter)
            boxes.append(new_box)
            text_boxes.append(new_box)

        cur_sentences += 1

    text_boxes.sort(key=lambda box: box.y)

    return img, [t.text for t in text_boxes]


def generate_dataset(num_images, directory, img_size):
    """
    :param num_images: Integer quantity of images to generate
    :param directory: relative location to save images in (include trailing slash)
    :param img_size: (width, height) of the image
    :return: None
    """

    with open(directory + "_labels.csv", "w", encoding="UTF8") as file:
        writer = csv.writer(file, delimiter="—", quotechar=" ", quoting=csv.QUOTE_MINIMAL)

        for i in range(num_images):
            new_image, label = generate_image(img_size)
            new_image.save(directory + str(i) + ".png")

            writer.writerow(label)


if __name__ == "__main__":
    generate_dataset(1, "../out/", (1920, 1080))

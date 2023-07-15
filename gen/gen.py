from perlin_numpy import generate_perlin_noise_2d
from essential_generators import DocumentGenerator
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
import random
import re
import os

from pos import TextBox
from pos import get_position


def get_sentence():
    gen = DocumentGenerator()

    sentence = gen.sentence()
    sentence = sentence.replace("–", "-").replace("—", "-").replace("−", "-")
    sentence = re.sub("[\s]+", " ", sentence)
    sentence = re.sub("[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]", "", sentence)

    return sentence


def generate_image(img_height, img_width, noise_scale):
    """
    Generates an image with random text and a noise background.

    :param img_height: height of the image in pixels
    :param img_width: width of the image in pixels
    :param noise_scale: scale of perlin noise pattern (smaller is more zoomed in,must be multiples of respective axes)
    :return: the generated image
    """

    noise = (
            generate_perlin_noise_2d((img_height, img_width), noise_scale) * 255
    ).astype(np.uint8)

    img = Image.fromarray(noise)
    draw = ImageDraw.Draw(img)

    num_sentences = 8  # np.random.randint(1, 21)
    cur_sentences = 0

    text_boxes = []

    while cur_sentences < num_sentences:
        sentence = get_sentence()
        font = ImageFont.FreeTypeFont(
            "fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100)
        )
        while (draw.textbbox((0, 0), sentence, font=font, anchor="lt")[2] > img_width or draw.textbbox((0, 0), sentence, font=font, anchor="lt")[3] > img_height):
            font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100)
        )
        left, top, width, height = draw.textbbox(
            (0, 0), sentence, font=font, anchor="lt"
        )
        new_box = TextBox(0, 0, width, height, sentence, font)

        x_pos, y_pos = get_position(new_box, text_boxes, (img_width, img_height))
        new_box.x = x_pos
        new_box.y = y_pos

        if x_pos > -1 and y_pos > -1:
            # new_box = TextBox(sentence, x_pos, y_pos, width, height, font)
            fill, stroke = random.sample([0, 255], 2)
            draw.text(
                (x_pos, y_pos),
                new_box.text,
                font=new_box.font,
                fill=fill,
                stroke_width=random.choice([2, 6]),
                stroke_fill=stroke,
            )
            text_boxes.append(new_box)

        cur_sentences += 1

    return img


if __name__ == "__main__":
    new_img = generate_image(1080, 1920, (27, 48))
    # plt.imshow(new_img, cmap="gray")
    # plt.axis("off")
    # plt.show()
    new_img.save("idunno.png")

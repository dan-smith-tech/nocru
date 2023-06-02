from perlin_numpy import generate_fractal_noise_2d, generate_perlin_noise_2d
from essential_generators import DocumentGenerator
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import re
import os


class TextBox(object):
    def __init__(self, text="", x=0, y=0, x_height=0, y_height=0, font=""):
        self.text = text
        self.x = x
        self.y = y
        self.x_height = x_height
        self.y_height = y_height
        self.font = font


def no_collision_check(test_box, text_boxes):
    if not text_boxes:
        return True
    else:
        for compBox in text_boxes:
            if (test_box.x < compBox.x + compBox.x_height and
                    test_box.x + test_box.x_height > compBox.x and
                    test_box.y < compBox.y + compBox.y_height and
                    test_box.y + test_box.y_height > compBox.y):
                return False
        return True


def oob_check(test_box, img_height, img_width):
    if (test_box.y + test_box.y_height < img_height and
            test_box.x + test_box.x_height < img_width):
        return True
    else:
        return False


def generate_image(img_height, img_width):
    """
    Generates an image with random text and a noise background.

    :param img_height: height of the image in pixels
    :param img_width: width of the image in pixels
    :return: the generated image
    """

    div = np.random.randint(30, 51)
    noise = (generate_perlin_noise_2d((img_height, img_width), (img_height / div, img_width / div)) * 255).astype(np.uint8)

    img = Image.fromarray(noise)
    draw = ImageDraw.Draw(img)

    gen = DocumentGenerator()
    # number of lines to place around the image (max exclusive, min inclusive)
    ceil = np.random.randint(1, 21)
    count = 0
    text_boxes = []

    while count < ceil:
        sentence = gen.sentence()
        sentence = sentence.replace("–", "-").replace("—", "-").replace("−", "-")
        sentence = re.sub('[\s]+', " ", sentence)
        sentence = re.sub('[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]', "", sentence)

        try:
            font = ImageFont.truetype(random.choice(os.listdir("fonts/")), np.random.randint(30, 151))
            left, top, x_height, y_height = draw.multiline_textbbox((0, 0), sentence, font=font)
            x_height = left + x_height
            y_height = top + y_height
            new_box = TextBox(sentence, np.random.randint(0, img_width), np.random.randint(0, img_height), x_height,
                              y_height, font)

            if no_collision_check(new_box, text_boxes) and oob_check(new_box, img_height, img_width):
                a, b = random.sample([0, 255], 2)
                draw.text((new_box.x, new_box.y), new_box.text, font=new_box.font, fill=a,
                          stroke_width=random.choice([0, 10]), stroke_fill=b)
                text_boxes.append(new_box)
                count += 1
            else:
                print("Colliding with existing, skipping")
        except:
            print("Skipping due to encoding error")
            print(sentence)

    return img


if __name__ == "__main__":
    print("Number of images to generate:")
    number = int(input())
    totalCount = 0

    while totalCount < number:
        new_img = generate_image(1080, 1920)
        new_img.show()
        totalCount += 1

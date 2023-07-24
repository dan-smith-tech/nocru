from essential_generators import DocumentGenerator
from perlin_numpy import generate_perlin_noise_2d
from PIL import Image, ImageDraw, ImageFont
from decouple import config
import multiprocessing
import numpy as np
import random
import ftplib
import json
import time
import cv2
import io
import re
import os

from pos import get_position
from pos import TextBox

fonts_list = []

for f in os.listdir("fonts/"):
    fonts_list.append(ImageFont.FreeTypeFont("fonts/" + f, 10))

class Generator(multiprocessing.Process):
    def __init__(self, thread_id, size, begin, directory):
        multiprocessing.Process.__init__(self)
        self.thread_id = thread_id
        self.size = size
        self.begin = begin
        self.directory = directory

    def run(self):
        for i in range(self.begin, self.begin + self.size):
            new_image, text_boxes = generate_image()
            new_image.save(self.directory + str(i) + ".png")

            label = {
                "id": i,
                "text_boxes": [box.__dict__ for box in text_boxes]
            }

            with open(self.directory + str(i) + '.json', 'w', encoding='utf-8') as f:
                json.dump(label, f, cls=NpTypeEncoder, ensure_ascii=False, indent=4)


class GeneratorFTP(multiprocessing.Process):
    def __init__(self, thread_id, size, begin, address, username, password, directory):
        multiprocessing.Process.__init__(self)
        self.thread_id = thread_id
        self.size = size
        self.begin = begin
        self.address = address
        self.username = username
        self.password = password
        self.directory = directory

    def run(self):
        session = ftplib.FTP(self.address, self.username, self.password)
        session.cwd(self.directory)
        for i in range(self.begin, self.begin + self.size):
            print(self.thread_id + " generating " + str(i))
            new_image, text_boxes = generate_image()

            print(self.thread_id + " converting " + str(i))
            # convert Image to byte buffer
            _, image_buffer = cv2.imencode('.png', np.array(new_image))
            image_buffer_io = io.BytesIO(image_buffer)

            label = {
                "id": i,
                "text_boxes": [box.__dict__ for box in text_boxes]
            }

            print(self.thread_id + " jsondump " + str(i))
            label_json = json.dumps(label, cls=NpTypeEncoder, ensure_ascii=False, indent=4).encode()

            # convert json label to byte buffer
            print(self.thread_id + " json to buffer " + str(i))
            label_json_buffer_io = io.BytesIO(label_json)

            print(self.thread_id + " writing " + str(i))
            if str(i) + ".png" in session.nlst():
                print("!!!!!TRYING TO WRITE TO EXISTING FILE!!!!")
            session.storbinary('STOR ' + str(i) + ".png", image_buffer_io)
            session.storbinary('STOR ' + str(i) + ".json", label_json_buffer_io)
            # close IO buffers
            image_buffer_io.close()
            label_json_buffer_io.close()
            print(self.thread_id + " completed " + str(i))
        session.quit()


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

    font = random.choice(fonts_list)
    # font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100))

    # makes sure sentence isnt literally too wide for the image. retries if it is.
    while (draw.textbbox((0, 0), sentence, font=font, anchor="lt")[2] > img_size[0] or
           draw.textbbox((0, 0), sentence, font=font, anchor="lt")[3] > img_size[1]):
        font = random.choice(fonts_list)
        # font = ImageFont.FreeTypeFont("fonts/" + random.choice(os.listdir("fonts/")), np.random.randint(50, 100))
    # setattr(font, 'size', np.random.randint(50, 100))
    font1 = font
    font1.size = np.random.randint(50, 100)
    return font1


def create_textbox(existing_boxes, draw, img_size):
    """
    Generates a TextBox to be placed on an image.

    :param existing_boxes: [TextBox] of the current boxes placed on the image
    :param draw: ImageDraw (mutated) that holds the current state of the image being generated
    :param img_size: (width, height) of the image
    :return: TextBox of the new text placed on the image
    """

    print("sentence")
    sentence = get_sentence()
    print("font")
    font = get_font(sentence, draw, img_size)

    print("bbox")
    left, top, width, height = draw.textbbox((0, 0), sentence, font=font, anchor="lt")
    color, stroke_color = random.sample([0, 255], 2)
    stroke_width = random.choice([2, 6])
    new_box = TextBox(0, 0, width, height, sentence, font, color, stroke_width, stroke_color)
    
    print("position")
    x_pos, y_pos = get_position(new_box, existing_boxes, (img_size[0], img_size[1]))
    new_box.x = x_pos
    new_box.y = y_pos

    print("overlap")
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

    print("perlin")
    noise = (generate_perlin_noise_2d((img_size[1], img_size[0]), noise_scale) * 255).astype(np.uint8)
    print("array")
    img = Image.fromarray(noise)
    print("draw")
    draw = ImageDraw.Draw(img)
    text_boxes = []

    print("boxes")
    for i in range(random.randrange(8)):
        print("create box")
        new_box = create_textbox(text_boxes, draw, img_size)

        print("fit")
        # if the text fits on the image somewhere, place it
        if new_box.x > -1 and new_box.y > -1:
            draw.text((new_box.x, new_box.y), new_box.text, font=new_box.font, fill=new_box.color,
                      stroke_width=new_box.stroke_width, stroke_fill=new_box.stroke_color)
            # change FreeTypeFont to (name, weight) of font
            new_box.font = new_box.font.getname()

            print("cutter")
            # if there is a cutter associated with this text box, place it
            if new_box.cutter_x:
                draw.rectangle((new_box.cutter_x, new_box.cutter_y, new_box.cutter_x + new_box.cutter_width,
                                new_box.cutter_y + new_box.cutter_height),
                               fill=new_box.cutter_color, outline=None, width=1)
            print("append")
            text_boxes.append(new_box)
    print("boxes done")
    return img, text_boxes


def generate_dataset(size, directory, begin=0, threads=6):
    """
    :param size: Integer quantity of images to generate
    :param begin: Integer index to begin generating at
    :param threads: Integer quantity of threads to use
    """

    extra = size % threads #10
    segment_size = (size - extra) // threads #666

    active_threads = []

    for i in range(threads - 1):
        active_threads.append(
            GeneratorFTP(str(i), segment_size, begin + i * segment_size,
                         config("FILESYSTEM_ADDRESS"), config("FILESYSTEM_USERNAME"), config("FILESYSTEM_PASSWORD"), directory=directory)
        )
    active_threads.append(
        GeneratorFTP(str(threads - 1), segment_size + extra, begin + (threads - 1) * segment_size,
                     config("FILESYSTEM_ADDRESS"), config("FILESYSTEM_USERNAME"), config("FILESYSTEM_PASSWORD"), directory=directory)
    )

    for thread in active_threads:
        thread.start()

    for thread in active_threads:
        thread.join()


def init():
    directory = input("Directory: ")
    size = int(input("Size of dataset: "))
    begin = int(input("Start index: "))
    threads = int(input("Number of threads: "))
    print("Dataset generating...")
    bt = time.time()
    generate_dataset(size, directory, begin=begin, threads=threads)
    et = time.time()
    print("Dataset completed in " + str(round(et - bt, 3)) + " seconds.")


if __name__ == "__main__":
    init()

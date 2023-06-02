import numpy as np
import os, random, re
from PIL import Image, ImageDraw, ImageFont
from perlin_numpy import (
    generate_fractal_noise_2d, generate_fractal_noise_3d,
    generate_perlin_noise_2d, generate_perlin_noise_3d
)
from essential_generators import DocumentGenerator

class textBox(object):
    def __init__(self, text="", x = 0, y = 0, xH = 0, yH = 0, textFont = ""):
        self.text = text
        self.x = x
        self.y = y
        self.xH = xH
        self.yH = yH
        self.textFont = textFont

def notCollisionCheck(testBox):
    if (not texts):
        return True
    else:
        for compBox in texts:
            if(testBox.x < compBox.x + compBox.xH and
            testBox.x + testBox.xH > compBox.x and
            testBox.y < compBox.y + compBox.yH and
            testBox.y + testBox.yH > compBox.y):
                return False
        return True

def OOBcheck(testBox):
    if (testBox.y + testBox.yH < imgY and
        testBox.x + testBox.xH < imgX):
        return True
    else:
        return False

imgX = 1920
imgY = 1080

# # white noise
# rng = np.random.default_rng()
# rints = rng.integers(low=0, high=257, size=(1080, 1920))

# # rints = np.random.randint(0, 257, size=(1080, 1920, 3))
# rints = (rints * 255).astype(np.uint8)

print("number of products to make:")
number = int(input())
totalCount = 0

while totalCount < number:
    np.random.seed(0)
    # makes background image. last two numbers define scale of pattern. smaller is more zoomed in. must be multiples of respective axes
    # rints = generate_perlin_noise_2d((imgY, imgX), (108, 192))
    rints = generate_perlin_noise_2d((imgY, imgX), (27, 48))
    rints = (rints * 255).astype(np.uint8)

    img = Image.fromarray(rints)
    draw = ImageDraw.Draw(img)

    gen = DocumentGenerator()
    # number of lines to place around the image. max exclusive, min inclusive
    ceil = np.random.randint(1, 21)
    count = 0
    texts = []
    while count < ceil:
        sentence = gen.sentence()
        sentence = sentence.replace("–", "-").replace("—", "-").replace("−", "-")
        sentence = re.sub('[\s]+', " ", sentence)
        sentence = re.sub('[^\u0020-\u007E0-9\u00A0-\u00FF$¢£¤¥₣₤₧₪₫€₹₽₿!?]', "", sentence)
        try:
            textFont = ImageFont.truetype(random.choice(os.listdir("fonts/")), np.random.randint(30, 151))
            l, t, xH, yH = draw.multiline_textbbox((0,0), sentence, font=textFont)
            xH = l + xH
            yH = t + yH
            newBox = textBox(sentence, np.random.randint(0, imgX), np.random.randint(0, imgY), xH, yH, textFont)
            if(notCollisionCheck(newBox) and OOBcheck(newBox)):
                a, b = random.sample([0, 255], 2)
                draw.text((newBox.x, newBox.y), newBox.text, font=newBox.textFont, fill=a, stroke_width=random.choice([0, 10]), stroke_fill=b)
                texts.append(newBox)
                count += 1
            else:
                print("Colliding with existing, skipping")
        except:
            print("Skipping due to encoding error")
            print(sentence)

    # img.show()
    img.save("output/" + str(totalCount) + ".png")
    totalCount += 1
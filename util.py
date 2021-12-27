from PIL import Image, ImageDraw

import os
import re
import json

configuration = json.loads(
    open("config.json", 'r').read()
)

configuration["role_position"] = int(open("position.txt").read())


def make_image(dominant_color):
    image = Image.new(mode="RGBA", size=(50, 50),
                      color=(0, 0, 0, 0))
    ImageDraw.Draw(
        image
    ).rounded_rectangle((0, 0, 50, 50), radius=20, fill=dominant_color)

    return image


def clean_up():
    if os.path.exists("palette.png"):
        os.remove("palette.png")


def concatenate_images(images):
    image = Image.new(mode="RGBA", size=(50 * 10, 50),
                      color=(0, 0, 0, 0))
    ImageDraw.Draw(image).rounded_rectangle(
        (0, 0, 500, 256), radius=20)

    width = 0
    for image_to_paste in images:
        image.paste(image_to_paste, (width, 0))
        width += 50

    image.save("palette.png", "PNG")


def rgb_to_hex(rgb):
    return "%02x%02x%02x" % (rgb)


def match_url_regex(string):
    # It works 🤷‍♀️
    return re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', string)


def update_role_position(modifier):
    if modifier == "increment":
        configuration["role_position"] += 1
    else:
        configuration["role_position"] -= 1

    with open("position.txt", 'w') as file:
        file.write(str(configuration["role_position"]))

from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import urllib.request as request
import urllib.error

IMAGE_SIZE = (500, 500)
WATERMARK = Image.open("img/watermark.png")
# Mismatching widths between image size and watermark will stretch the watermark
if WATERMARK.size[0] != IMAGE_SIZE[0]:
    WATERMARK = WATERMARK.resize((IMAGE_SIZE[0], WATERMARK.size[1]), Image.BICUBIC)

# Gets a list of image url, image type tuples using the search query.
def get_google_images(query):
    query = query.replace(' ', '+')
    url = "https://www.google.com/search?q=" + query + "&source=lnms&tbm=isch"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
    content = request.urlopen(request.Request(url, headers=headers))
    soup = BeautifulSoup(content, "html5lib")
    imgs = []
    for div in soup.find_all("div", {"class": "rg_meta"}):
        metadata = json.loads(div.text)
        imgurl, typ = metadata["ou"], metadata["ity"]
        imgs.append((imgurl, typ))
    return imgs

# Gets a PIL image from the url.
def get_image_from_url(url):
    try:
        content = request.urlopen(url).read()
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(e)
        return None
    else:
        f = BytesIO(content)
        img = Image.open(f).copy()
        f.close()
        return img

def resize_width_keep_aspect(img, width_new):
    width, height = img.size
    height_new = width_new * height // width
    return img.resize((width_new, height_new), Image.BICUBIC)

# Creates a text meme using text.
def create_text_meme(text):
    ret_img = Image.new("RGBA", IMAGE_SIZE)

    # Prepare drawing the text
    freesans = ImageFont.truetype("font/FreeSans.ttf", 24)
    draw = ImageDraw.Draw(ret_img)
    for char_width in range(60, 1, -1):
        new_text = '\n'.join(textwrap.wrap(text, width=char_width))
        width, height = draw.multiline_textsize(new_text, freesans)
        if width <= IMAGE_SIZE[0]-20:
            break
    del draw

    # Resize the image based on the text size and then draw it
    ret_img = ret_img.resize((IMAGE_SIZE[0],
        max(IMAGE_SIZE[1],height)+20+WATERMARK.size[1]))
    # Fill with white before drawing text
    ret_img.paste("white", (0, 0, ret_img.size[0], ret_img.size[1]))
    # Then draw the text
    draw = ImageDraw.Draw(ret_img)
    draw.multiline_text((10,ret_img.size[1]//2 - height//2),
        new_text, fill="black", font=freesans)
    del draw

    # Finally, paste the watermark
    ret_img.paste(WATERMARK, (0, ret_img.size[1]-WATERMARK.size[1]),
        mask=WATERMARK)

    return ret_img

# Creates a Twitter-like text+image meme using text and the image at imgurl.
def create_text_with_image_meme(text, imgurl):
    inside_img = get_image_from_url(imgurl)
    if not inside_img:
        return None
    
    ret_img = Image.new("RGBA", IMAGE_SIZE)
    
    # First, fill with white
    ret_img.paste("white", (0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]))

    # Draw the text
    draw = ImageDraw.Draw(ret_img)
    font_sizes = range(24, 8, -1)
    # Increment the amt of characters per line quadratically from 48-104 chars
    char_widths = (48 + int(4*(x*x - x)/15) for x in range(16))
    for font_size, char_width in zip(font_sizes, char_widths):
        new_text = '\n'.join(textwrap.wrap(text, width=char_width))
        freesans = ImageFont.truetype("font/FreeSans.ttf", font_size)
        width, height = draw.multiline_textsize(new_text, freesans)
        if width <= IMAGE_SIZE[0]-20 and height <= IMAGE_SIZE[1]//3-20:
            break
    inside_img_top = height + 20
    draw.multiline_text((10,10), new_text, fill="black", font=freesans)
    del draw

    # Paste the related image
    inside_img = resize_width_keep_aspect(inside_img, IMAGE_SIZE[0])
    # If height is greater than remaining size, crop it to fit
    if inside_img.size[1] > IMAGE_SIZE[1] - inside_img_top:
        inside_img = inside_img.crop((0, inside_img_top//2,
            IMAGE_SIZE[0], IMAGE_SIZE[1]-inside_img_top//2))
    ret_img.paste(inside_img, (0, inside_img_top))

    # If the pasted image leaves a lot of whitespace, crop it
    if inside_img_top + inside_img.size[1] < IMAGE_SIZE[1]:
        ret_img = ret_img.crop((0, 0, IMAGE_SIZE[0],
            inside_img_top + inside_img.size[1]))

    # Finally, paste the watermark
    ret_img.paste(WATERMARK, (0, ret_img.size[1]-WATERMARK.size[1]),
        mask=WATERMARK)

    return ret_img
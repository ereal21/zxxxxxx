
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, string, io

_ALPHABET = string.ascii_uppercase + string.digits

def _text_size(draw, text, font):
    # Pillow 10+: draw.textbbox; fallback to font.getbbox; last resort estimate
    try:
        left, top, right, bottom = draw.textbbox((0,0), text, font=font)
        return right - left, bottom - top
    except Exception:
        try:
            bbox = font.getbbox(text)
            return bbox[2]-bbox[0], bbox[3]-bbox[1]
        except Exception:
            return (len(text) * 12, 20)

def random_text(length=5):
    return ''.join(random.choice(_ALPHABET) for _ in range(length))

def generate_captcha(text=None, width=220, height=80):
    text = text or random_text()
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try to use a nicer font if available, else default
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    # Background noise
    for _ in range(200):
        x, y = random.randint(0, width-1), random.randint(0, height-1)
        draw.point((x, y), fill=(random.randint(180,255),)*3)

    # Disturbing lines
    for _ in range(8):
        x1, y1, x2, y2 = [random.randint(0, width) for _ in range(4)]
        draw.line(((x1,y1),(x2,y2)), width=1)

    # Draw text with slight jitter per character
    tw, th = _text_size(draw, text, font)
    start_x = (width - tw) // 2
    start_y = (height - th) // 2
    x = start_x
    for ch in text:
        y = start_y + random.randint(-2, 2)
        draw.text((x, y), ch, font=font, fill=(0,0,0))
        cw, _ = _text_size(draw, ch, font)
        x += cw + random.randint(0, 2)

    img = img.filter(ImageFilter.GaussianBlur(0.6))

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue(), text

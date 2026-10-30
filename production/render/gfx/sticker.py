"""Emoji / text stickers with a white die-cut border and soft shadow, as RGBA PNGs."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
def emoji(ch, size=220, border=10):
    f = ImageFont.truetype(EMOJI, 109)             # CBDT font only renders at 109 px
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
    im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS) if im.getbbox() else im
    return die_cut(im, border)
def die_cut(im, border=10, shadow=True):
    pad = border * 3
    c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); c.paste(im, (pad, pad), im)
    a = c.split()[3].point(lambda v: 255 if v > 40 else 0)
    outline = a.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    white = Image.new('RGBA', c.size, (255, 255, 255, 255)); white.putalpha(outline)
    out = Image.new('RGBA', c.size, (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', c.size, (0, 0, 0, 255)); sh.putalpha(outline.point(lambda v: int(v * 0.45)).filter(ImageFilter.GaussianBlur(8)))
        out.alpha_composite(sh, (4, 8))
    out.alpha_composite(white); out.alpha_composite(c)
    return out
def text_sticker(text, font_path, size=64, fg=(20, 20, 24), bg=(255, 212, 0), rot=-4, border=8):
    f = ImageFont.truetype(font_path, size)
    d = ImageDraw.Draw(Image.new('RGB', (1, 1))); l, t, r, b = d.textbbox((0, 0), text, font=f)
    padx, pady = int(size * 0.45), int(size * 0.28)
    im = Image.new('RGBA', (r - l + 2 * padx, b - t + 2 * pady), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=int(size * 0.35), fill=bg)
    dd.text((padx - l, pady - t), text, font=f, fill=fg)
    im = die_cut(im, border)
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)
if __name__ == '__main__':
    import sys
    bg = Image.new('RGBA', (1200, 400), (60, 90, 140, 255))
    for k, ch in enumerate('🔥🤖🐑😂🤯📸'): bg.alpha_composite(emoji(ch, 150), (20 + k * 190, 20))
    bg.alpha_composite(text_sticker('NOT CGI', '/usr/share/fonts/opentype/inter/Inter-Bold.otf', 60), (60, 240))
    bg.save(sys.argv[1])

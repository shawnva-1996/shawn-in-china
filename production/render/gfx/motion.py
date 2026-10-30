"""Tiny motion-graphics engine: layers of RGBA images with pop / slide / fade / count-up / draw-on
animations, rendered to a transparent MOV (PNG codec) that ffmpeg 4.4 can overlay.
Every graphic is a list of Layer objects; render(layers, dur, path) writes the clip."""
import os
import math, subprocess
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1920, 1080, 30
ANTON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'Anton.ttf')   # SIL OFL
INTER = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
INTERB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
INTERX = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
CJK = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
YEL = (255, 212, 0); INK = (16, 17, 22)
def font(p, s): return ImageFont.truetype(p, s)
def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def back_out(x, s=2.2):
    x = min(1, max(0, x)); x -= 1; return x * x * ((s + 1) * x + s) + 1
class Layer:
    """img: RGBA image or callable(progress)->RGBA. (x, y) is the centre. anim in: pop | slide-up | slide-left |
    slide-right | fade | none. t0 = entrance time; out = exit time (fade+shrink); wiggle = gentle sticker bob."""
    def __init__(self, img, x, y, t0=0.0, anim='pop', dur=0.45, out=None, wiggle=False, rot=0):
        self.img, self.x, self.y, self.t0, self.anim, self.dur, self.out, self.wiggle, self.rot = img, x, y, t0, anim, dur, out, wiggle, rot
    def frame(self, t):
        if t < self.t0: return None
        p = (t - self.t0) / self.dur
        im = self.img(t - self.t0) if callable(self.img) else self.img
        a, sc, dx, dy = 1.0, 1.0, 0, 0
        if self.anim == 'pop': sc = back_out(p) if p < 1 else 1; a = min(1, p * 3)
        elif self.anim == 'slide-up': dy = (1 - ease_out(p)) * 60; a = ease_out(p)
        elif self.anim == 'slide-left': dx = (1 - ease_out(p)) * 120; a = ease_out(p)
        elif self.anim == 'slide-right': dx = -(1 - ease_out(p)) * 120; a = ease_out(p)
        elif self.anim == 'fade': a = ease_out(p)
        if self.out is not None and t > self.out:
            q = min(1, (t - self.out) / 0.3); a *= 1 - q; sc *= 1 - 0.15 * q
        if a <= 0.01 or sc <= 0.02: return None
        rot = self.rot + (math.sin((t - self.t0) * 2.4) * 2.5 if self.wiggle else 0)
        if sc != 1 or rot: 
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
            if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        if a < 1: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
        return im, int(self.x + dx - im.width / 2), int(self.y + dy - im.height / 2)
def render(layers, dur, path, bg=None):
    """bg: None for a transparent overlay, or an RGB colour / RGBA image for a full-screen card."""
    n = int(round(dur * FPS))
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    cmd += (['-c:v', 'png', '-pix_fmt', 'rgba', path] if bg is None else ['-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path])
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        if bg is None: fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        elif isinstance(bg, Image.Image): fr = bg.copy().convert('RGBA')
        else: fr = Image.new('RGBA', (W, H), bg + (255,))
        for L in layers:
            r = L.frame(t)
            if r: fr.alpha_composite(r[0], (max(-r[0].width, r[1]), max(-r[0].height, r[2]))) if r[1] >= 0 and r[2] >= 0 else _paste(fr, *r)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close(); pr.wait()
def _paste(fr, im, x, y):
    c = Image.new('RGBA', fr.size, (0, 0, 0, 0)); c.paste(im, (x, y), im); fr.alpha_composite(c)
# ---------- building blocks ----------
def pill(text, size=46, fg='white', bg=(16, 17, 22, 225), fnt=INTERB, pad=(30, 16), accent=None, radius=None):
    f = font(CJK if any('一' <= ch <= '鿿' for ch in text) else fnt, size)
    d = ImageDraw.Draw(Image.new('RGB', (1, 1))); l, t, r, b = d.textbbox((0, 0), text, font=f)
    acc = 12 if accent else 0
    im = Image.new('RGBA', (r - l + 2 * pad[0] + acc, b - t + 2 * pad[1]), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius or int(size * 0.32), fill=bg)
    if accent: dd.rounded_rectangle([0, 0, acc + 6, im.height - 1], radius=4, fill=accent); dd.rectangle([acc, 0, acc + 6, im.height - 1], fill=bg)
    dd.text((pad[0] + acc - l, pad[1] - t), text, font=f, fill=fg)
    return im
def big_text(text, size=160, fill=YEL, stroke=8, fnt=ANTON, stroke_fill=INK):
    f = font(fnt, size); d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    l, t, r, b = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - l, 10 - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im
def counter(value, dur=1.2, size=170, fmt='{:,.0f}', suffix='', fill=YEL):
    """returns callable(t)->image counting 0 -> value with ease-out"""
    cache = {}
    def f(t):
        v = value * ease_out(t / dur)
        s = fmt.format(v) + suffix
        if s not in cache: cache[s] = big_text(s, size, fill)
        return cache[s]
    return f

# ---------- mixed text: Latin (Inter/Anton) + CJK (WenQuanYi) + colour emoji (Noto) ----------
import re as _re
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
_EMO = _re.compile('(?:[\U0001F1E6-\U0001F1FF]{2}|[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌚-⏿](?:️)?(?:[\U0001F3FB-\U0001F3FF])?(?:‍[\U0001F000-\U0001FAFF☀-➿](?:️)?)*)')
_CJK = _re.compile('[　-〿一-鿿＀-￯]+')
_KEEP = set('✓→↔')          # drawn as text, not emoji
def _emoji_img(cl, px):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new('RGBA', (180, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((90, 80), cl, font=f, embedded_color=True, anchor='mm')
    bb = im.getbbox(); im = im.crop(bb) if bb else im
    return im.resize((max(1, int(im.width * px / 109)), max(1, int(im.height * px / 109))), Image.LANCZOS)
def rich(text, size, fill='white', fnt=INTERB, stroke=0, stroke_fill=INK):
    runs, i = [], 0
    while i < len(text):
        m = _EMO.match(text, i)
        if m and text[i] not in _KEEP: runs.append(('e', m.group())); i = m.end(); continue
        m = _CJK.match(text, i)
        if m: runs.append(('c', m.group())); i = m.end(); continue
        j = i
        while j < len(text) and not (_EMO.match(text, j) and text[j] not in _KEEP) and not _CJK.match(text, j): j += 1
        runs.append(('t', text[i:j])); i = j
    fonts = {'t': font(fnt, size), 'c': font(CJK, int(size * 1.02))}
    asc = fonts['t'].getmetrics()[0]; Hh = int(size * 1.45) + 2 * stroke
    parts = []
    for k, s in runs:
        if k == 'e':
            parts.append(_emoji_img(s, int(size * 1.05)))
        else:
            f = fonts[k]; d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            w = int(d.textlength(s, font=f)) + 2 * stroke
            im = Image.new('RGBA', (max(1, w), Hh), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((stroke, int(size * 0.12) + stroke), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            parts.append(im)
    gap = int(size * 0.08)
    out = Image.new('RGBA', (sum(p.width for p in parts) + gap * (len(parts) - 1), Hh), (0, 0, 0, 0)); x = 0
    for (k, s), p in zip(runs, parts):
        out.alpha_composite(p, (x, (Hh - p.height) // 2 if k == 'e' else 0)); x += p.width + gap
    bb = out.getbbox()
    return out.crop((0, 0, out.width, Hh)) if bb else out
def rpill(text, size=46, fg='white', bg=(16, 17, 22, 225), fnt=INTERB, pad=(30, 12), accent=None):
    t = rich(text, size, fg, fnt)
    acc = 12 if accent else 0
    im = Image.new('RGBA', (t.width + 2 * pad[0] + acc, t.height + 2 * pad[1]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=int(size * 0.38), fill=bg)
    if accent: d.rounded_rectangle([0, 0, acc + 8, im.height - 1], radius=int(size * 0.38), fill=accent); d.rectangle([acc, 0, acc + 8, im.height - 1], fill=bg)
    im.alpha_composite(t, (pad[0] + acc, pad[1]))
    return im

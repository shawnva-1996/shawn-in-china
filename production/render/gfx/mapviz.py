"""'East Data, West Computing' animated map: coastline only (no borders), east-coast demand cities
pulse, arrows draw west to Chongqing. Uses world-atlas land-50m (npm) topojson."""
import json, math
from PIL import Image, ImageDraw, ImageFilter
from motion import W, H, FPS, font, ANTON, INTERB, INTER, CJK, YEL, ease_out, Layer, render, pill
LON0, LON1, LAT0, LAT1 = 92.0, 131.0, 14.0, 49.0      # frame: Sichuan basin to the east coast
def proj(lon, lat):
    x = (lon - LON0) / (LON1 - LON0) * W
    y = (1 - (math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) - math.log(math.tan(math.pi / 4 + math.radians(LAT0) / 2))) /
         (math.log(math.tan(math.pi / 4 + math.radians(LAT1) / 2)) - math.log(math.tan(math.pi / 4 + math.radians(LAT0) / 2)))) * H
    return x, y
def land(topo_path):
    tj = json.load(open(topo_path)); sc, tr = tj['transform']['scale'], tj['transform']['translate']
    arcs = []
    for arc in tj['arcs']:
        x = y = 0; pts = []
        for dx, dy in arc: x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    def ring(idx):
        out = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out += a[1:] if out else a
        return out
    polys = []
    for g in tj['objects']['land']['geometries']:
        cs = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        for poly in cs: polys.append(ring(poly[0]))
    return polys
def base(topo_path):
    im = Image.new('RGBA', (W, H), (12, 16, 26, 255)); d = ImageDraw.Draw(im)
    for r in land(topo_path):
        if not any(LON0 - 10 < lo < LON1 + 10 and LAT0 - 10 < la < LAT1 + 10 for lo, la in r): continue
        d.polygon([proj(lo, la) for lo, la in r], fill=(34, 44, 62, 255), outline=(70, 90, 120, 255))
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(top).rectangle([0, 0, W, 250], fill=(12, 16, 26, 170))
    im.alpha_composite(top)
    return im
EAST = [('Beijing', 116.4, 39.9), ('Shanghai', 121.47, 31.23), ('Shenzhen', 114.06, 22.54)]
CQ = ('Chongqing', 106.55, 29.56)
def arrows(t0):
    def f(t):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for k, (n, lo, la) in enumerate(EAST):
            p = ease_out((t - k * 0.25) / 1.1)
            if p <= 0: continue
            (x0, y0), (x1, y1) = proj(lo, la), proj(*CQ[1:])
            cx, cy = (x0 + x1) / 2, min(y0, y1) - 160          # arc control point
            pts = []
            for i in range(int(60 * p) + 1):
                s = i / 60; pts.append(((1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s * s * x1, (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cy + s * s * y1))
            if len(pts) > 1: d.line(pts, fill=YEL + (255,), width=7, joint='curve')
            if p >= 1:
                (ax, ay), (bx, by) = pts[-6], pts[-1]; ang = math.atan2(by - ay, bx - ax)
                d.polygon([(bx, by), (bx - 34 * math.cos(ang - 0.45), by - 34 * math.sin(ang - 0.45)), (bx - 34 * math.cos(ang + 0.45), by - 34 * math.sin(ang + 0.45))], fill=YEL + (255,))
        return im
    return Layer(f, W // 2, H // 2, t0, 'none')
def dot(lo, la, r, col, glow=False):
    s = r * 6; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if glow: d.ellipse([s / 2 - r * 2.4, s / 2 - r * 2.4, s / 2 + r * 2.4, s / 2 + r * 2.4], fill=col[:3] + (70,)); im = im.filter(ImageFilter.GaussianBlur(r * 0.6)); d = ImageDraw.Draw(im)
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=col)
    x, y = proj(lo, la); return im, x, y
def build(topo_path, out, dur=9.0, t_cities=0.4, t_demand=0.9, t_west=3.3):
    """t_cities / t_demand / t_west: when the east-coast cities, the demand label and the westward arrows land
    (pass the VO word times so the map moves with the narration)."""
    L = []
    for k, (n, lo, la) in enumerate(EAST):
        im, x, y = dot(lo, la, 16, (90, 170, 255, 255), glow=True); L.append(Layer(im, x, y, t_cities + k * 0.15, 'pop'))
        L.append(Layer(pill(n, 36, bg=(16, 17, 22, 200)), x + 120, y - 40, t_cities + 0.2 + k * 0.15, 'fade'))
    L.append(Layer(pill('DEMAND IS IN THE EAST', 40, fg=(150, 200, 255), bg=(16, 17, 22, 0)), *proj(124.5, 27.0), t_demand, 'fade'))
    L.append(arrows(t_west - 1.3))
    im, x, y = dot(*CQ[1:], 26, YEL + (255,), glow=True); L.append(Layer(im, x, y, t_west, 'pop'))
    L.append(Layer(pill('Chongqing · data centres', 44, fg=INK_ if (INK_ := (16, 17, 22)) else 'black', bg=YEL + (255,)), x - 60, y + 90, t_west + 0.2, 'pop'))
    L.append(Layer(pill('cheaper land + power in the west', 34, bg=(16, 17, 22, 210)), x - 40, y + 170, t_west + 0.8, 'slide-up'))
    from motion import big_text
    L.append(Layer(big_text('EAST DATA, WEST COMPUTING', 92, fill=(255, 255, 255), stroke=6), W // 2, 92, 0.0, 'slide-up'))
    L.append(Layer(big_text('东数西算', 58, fill=YEL, stroke=4, fnt=CJK), W // 2, 186, 0.25, 'slide-up'))
    render(L, dur, out, bg=base(topo_path))
if __name__ == '__main__':
    import sys; build(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 9.0)

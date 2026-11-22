#!/usr/bin/env python3
"""The picture that tastes of one ingredient - steaming bowl of ramen.

Stdlib only. Renders at 2x (2048) and downsamples to 1024x1024,
writes a PNG to /output/entry.png with a hand-rolled encoder.
Deterministic: fixed seed / fixed geometry, no randomness from time.
"""
import math
import struct
import zlib

OUT_W = 1024
S = 2                      # supersample factor
W = OUT_W * S
H = OUT_W * S
OUT_PATH = "/output/entry.png"

# ---------------------------------------------------------------- helpers
def _crc(data):
    return zlib.crc32(data) & 0xFFFFFFFF

def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", _crc(tag + data))

def write_png(path, w, h, rgb):
    """rgb: bytes of w*h*3. Minimal PNG encoder, filter 0 per row."""
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", idat)
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# deterministic pseudo-random in [0,1)
def rnd(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)

class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def px(self, x, y):
        i = (y * self.w + x) * 3
        return self.buf[i], self.buf[i + 1], self.buf[i + 2]

    def hline(self, y, x0, x1, col):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0)); x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        i = (y * self.w + x0) * 3
        n = x1 - x0 + 1
        self.buf[i:i + n * 3] = bytes(col) * n

    def fill_ellipse(self, cx, cy, rx, ry, col, y0=None, y1=None):
        lo = max(0, int(cy - ry)) if y0 is None else max(0, int(y0))
        hi = min(self.h - 1, int(cy + ry)) if y1 is None else min(self.h - 1, int(y1))
        for y in range(lo, hi + 1):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            self.hline(y, cx - dx, cx + dx, col)

    def fill_ellipse_grad(self, cx, cy, rx, ry, c_in, c_out):
        """Radial gradient ellipse, centre c_in -> edge c_out."""
        lo = max(0, int(cy - ry)); hi = min(self.h - 1, int(cy + ry))
        for y in range(lo, hi + 1):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            # blend factor by normalised distance of this row's centre
            t = min(1.0, abs(dy) * 0.85)
            col = tuple(int(c_in[k] + (c_out[k] - c_in[k]) * t) for k in range(3))
            self.hline(y, cx - dx, cx + dx, col)

    def disk(self, cx, cy, r, col):
        self.fill_ellipse(cx, cy, r, r, col)

    def blend_disk(self, cx, cy, r, col, alpha):
        """Alpha-blended disk (alpha 0..1)."""
        lo = max(0, int(cy - r)); hi = min(self.h - 1, int(cy + r))
        buf = self.buf; w = self.w
        for y in range(lo, hi + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0.0, r * r - dy * dy)))
            for x in range(max(0, int(cx - dx)), min(w - 1, int(cx + dx)) + 1):
                i = (y * w + x) * 3
                for k in range(3):
                    buf[i + k] = int(buf[i + k] * (1 - alpha) + col[k] * alpha)

    def blend_ellipse(self, cx, cy, rx, ry, col, alpha):
        lo = max(0, int(cy - ry)); hi = min(self.h - 1, int(cy + ry))
        buf = self.buf; w = self.w
        for y in range(lo, hi + 1):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
            for x in range(max(0, int(cx - dx)), min(w - 1, int(cx + dx)) + 1):
                i = (y * w + x) * 3
                for k in range(3):
                    buf[i + k] = int(buf[i + k] * (1 - alpha) + col[k] * alpha)

    def thick_line(self, x0, y0, x1, y1, r, col):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) / max(1, r // 2)) + 1
        for s in range(steps + 1):
            t = s / steps
            self.disk(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, col)

# ---------------------------------------------------------------- scene
def main():
    c = Canvas(W, H)

    # --- warm dark wooden table: vertical gradient + plank seams ---
    for y in range(H):
        t = y / H
        r = int(34 + 26 * t)
        g = int(22 + 16 * t)
        b = int(15 + 9 * t)
        # soft warm pool of light behind the bowl
        glow = math.exp(-((y - 1150) ** 2) / (2 * 700.0 ** 2)) * 14
        r = min(255, int(r + glow)); g = min(255, int(g + glow * 0.7)); b = min(255, int(b + glow * 0.4))
        c.hline(y, 0, W - 1, (r, g, b))
    # plank seams (horizontal, darker)
    for sy in (430, 880, 1560):
        for yy in range(sy, sy + 7):
            c.hline(yy, 0, W - 1, (20, 13, 9))
    # soft dark patches for wood depth
    c.blend_ellipse(300, 300, 420, 200, (12, 8, 6), 0.35)
    c.blend_ellipse(1850, 1850, 500, 260, (10, 7, 5), 0.35)

    # --- bowl: dark ceramic exterior, red rim, amber broth ---
    bx, by = 1024, 1230
    c.fill_ellipse(bx, by, 780, 520, (30, 30, 38))          # bowl body
    c.fill_ellipse(bx, by - 18, 780, 505, (22, 22, 30))     # shading
    c.fill_ellipse(bx, by, 700, 450, (168, 42, 32))         # red rim
    c.fill_ellipse(bx, by, 668, 420, (150, 34, 26))         # rim inner shade
    # broth with radial amber gradient
    c.fill_ellipse_grad(bx, by, 640, 395, (214, 132, 46), (146, 78, 24))
    # broth gloss: big soft highlight upper-left
    c.blend_ellipse(bx - 260, by - 150, 330, 130, (255, 196, 110), 0.38)
    c.blend_ellipse(bx - 300, by - 170, 150, 55, (255, 224, 160), 0.35)
    # chili-oil sheen: glossy red-orange pools on the broth
    c.blend_ellipse(bx + 260, by + 90, 210, 80, (198, 62, 18), 0.55)
    c.blend_ellipse(bx + 320, by + 120, 120, 45, (226, 96, 26), 0.5)
    c.blend_ellipse(bx - 380, by + 140, 130, 48, (190, 58, 16), 0.45)
    c.blend_ellipse(bx + 90, by - 260, 150, 50, (210, 72, 20), 0.4)

    # --- noodles: wavy springy strands across the broth ---
    noodle_hi = (244, 208, 132)
    noodle_lo = (198, 158, 88)
    for s in range(16):
        base_y = by - 300 + s * 42
        amp = 26 + rnd(s * 3 + 1) * 30
        ph = rnd(s * 7 + 2) * 6.28
        freq = 0.011 + rnd(s * 5 + 3) * 0.006
        # shadow strand slightly offset, then the lit strand
        for off, col in ((7, noodle_lo), (0, noodle_hi)):
            prev = None
            for x in range(bx - 560, bx + 560, 14):
                y = base_y + off + math.sin(x * freq + ph) * amp
                # keep strands inside the broth ellipse
                if ((x - bx) / 640) ** 2 + ((y - by) / 395) ** 2 > 0.92:
                    prev = None
                    continue
                if prev is not None:
                    c.thick_line(prev[0], prev[1], x, y, 11, col)
                prev = (x, y)

    # --- nori: dark green-black sheet tucked BEHIND the chashu ---
    c.fill_ellipse(1520, 1010, 105, 150, (16, 28, 18))
    c.fill_ellipse(1520, 1010, 94, 138, (22, 38, 24))

    # --- chashu: glistening pork slices, flatter ellipses, seared edge ---
    for (cx, cy, r) in ((1330, 1290, 155), (1450, 1150, 135), (1180, 1420, 125)):
        c.fill_ellipse(cx, cy, r, int(r * 0.78), (150, 74, 58))      # seared rim
        c.fill_ellipse(cx, cy, int(r * 0.92), int(r * 0.71), (206, 122, 96))
        c.fill_ellipse(cx, cy, int(r * 0.72), int(r * 0.55), (228, 162, 130))
        c.fill_ellipse(cx, cy, int(r * 0.42), int(r * 0.32), (240, 190, 156))
        c.blend_ellipse(cx - r * 0.3, cy - r * 0.32, int(r * 0.38), int(r * 0.16), (255, 222, 192), 0.55)
        # sesame seeds on the chashu
        for si in range(7):
            sx = cx - r * 0.6 + rnd(si * 31 + cx) * r * 1.2
            sy = cy - r * 0.45 + rnd(si * 17 + cy) * r * 0.9
            if ((sx - cx) / (r * 0.72)) ** 2 + ((sy - cy) / (r * 0.55)) ** 2 < 1:
                c.disk(sx, sy, 7, (250, 240, 220))

    # --- bowl foot (3/4 depth) ---
    c.fill_ellipse(bx, by + 470, 260, 42, (16, 16, 22))

    # --- soft-boiled eggs: white + jammy orange yolk (left side) ---
    for (cx, cy) in ((720, 1080), (830, 1330)):
        c.fill_ellipse(cx, cy, 128, 100, (246, 238, 224))
        c.fill_ellipse(cx, cy, 112, 86, (252, 246, 234))
        c.fill_ellipse(cx, cy, 62, 52, (232, 122, 28))
        c.fill_ellipse(cx - 8, cy - 6, 48, 40, (248, 152, 46))
        c.blend_ellipse(cx - 18, cy - 20, 26, 14, (255, 205, 110), 0.6)

    # --- scallions: little green rings scattered on the broth ---
    for i in range(28):
        cx = bx - 520 + rnd(i * 11 + 5) * 1040
        cy = by - 300 + rnd(i * 13 + 9) * 600
        if ((cx - bx) / 640) ** 2 + ((cy - by) / 395) ** 2 > 0.85:
            continue
        # avoid covering egg / chashu centres
        if ((cx - 720) ** 2 + (cy - 1080) ** 2 < 150 ** 2) or ((cx - 1330) ** 2 + (cy - 1290) ** 2 < 170 ** 2):
            continue
        r = 15 + rnd(i * 3 + 1) * 9
        c.disk(cx, cy, r, (74, 148, 62))
        c.disk(cx, cy, r * 0.55, (52, 112, 44))
        c.disk(cx, cy, r * 0.28, (150, 190, 90))

    # --- chopsticks lifting noodles (top right, diagonal) ---
    # noodle bundle draped from the chopstick tips down into the bowl
    for s in range(5):
        x0 = 1180 + s * 16
        y0 = 880 + s * 6
        prev = (x0, y0)
        for t in range(1, 41):
            tt = t / 40
            x = x0 + math.sin(tt * 5.2 + s) * 34 * tt + 40 * tt
            y = y0 + 300 * tt + math.sin(tt * 9 + s * 2) * 12
            c.thick_line(prev[0], prev[1], x, y, 10, noodle_hi if s % 2 == 0 else noodle_lo)
            prev = (x, y)
    # two chopsticks
    c.thick_line(1560, 260, 1170, 900, 20, (148, 98, 52))
    c.thick_line(1620, 330, 1230, 930, 20, (132, 86, 46))
    c.thick_line(1560, 260, 1170, 900, 9, (176, 124, 70))
    c.thick_line(1620, 330, 1230, 930, 9, (160, 110, 62))

    # --- steam: soft vertical wisps (few large tall shapes, low alpha, no rings) ---
    for col_i, sx in enumerate((860, 1024, 1190)):
        for k in range(3):
            y = 640 - k * 130
            x = sx + math.sin(k * 1.7 + col_i * 2.1) * 42
            c.blend_ellipse(x, y, 95 + k * 12, 210, (242, 238, 230), 0.055)
        c.blend_ellipse(sx + 20, 560, 55, 170, (250, 246, 240), 0.05)

    # --- bowl shadow on the table + bottom shading ---
    c.blend_ellipse(bx, by + 480, 720, 90, (8, 5, 4), 0.5)

    # --- downsample 2x -> 1024 with box average ---
    out = bytearray(OUT_W * OUT_W * 3)
    src = c.buf
    for oy in range(OUT_W):
        sy = oy * S
        for ox in range(OUT_W):
            sx = ox * S
            di = (oy * OUT_W + ox) * 3
            for k in range(3):
                s = 0
                for dy in range(S):
                    base = ((sy + dy) * W + sx) * 3 + k
                    s += src[base] + src[base + 3]
                out[di + k] = s // (S * S)
    # --- vignette + warm finish at 1024 ---
    cx0, cy0 = OUT_W / 2, OUT_W / 2
    for y in range(OUT_W):
        for x in range(OUT_W):
            dx = (x - cx0) / cx0
            dy = (y - cy0) / cy0
            d2 = dx * dx + dy * dy
            vig = 1.0 - 0.34 * max(0.0, d2 - 0.35) ** 1.2
            if vig < 1.0:
                i = (y * OUT_W + x) * 3
                for k in range(3):
                    out[i + k] = int(out[i + k] * vig)
    import os
    os.makedirs("/output", exist_ok=True)
    size = write_png(OUT_PATH, OUT_W, OUT_W, bytes(out))
    print(f"wrote {OUT_PATH} {size} bytes")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The picture that tastes of one ingredient — steaming ramen bowl.

Stdlib only. Renders at 2x (2048) with supersampling, downsamples to
1024x1024, writes /output/entry.png via a hand-rolled PNG encoder.
Deterministic: fixed seed, no time/network input.
"""
import math
import os
import random
import struct
import zlib

SEED = 20261122
SS = 2
OUT_W = 1024
OUT_H = 1024
W = OUT_W * SS
H = OUT_H * SS
OUT_PATH = "/output/entry.png"

rng = random.Random(SEED)

# ---------------------------------------------------------------- buffer
buf = bytearray(W * H * 3)


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend_px(x, y, r, g, b, a):
    """Blend colour over existing pixel, a in 0..1."""
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = (y * W + x) * 3
        if a >= 1.0:
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
        else:
            buf[i] = int(buf[i] * (1 - a) + r * a)
            buf[i + 1] = int(buf[i + 1] * (1 - a) + g * a)
            buf[i + 2] = int(buf[i + 2] * (1 - a) + b * a)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_c(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def fill_ellipse(cx, cy, rx, ry, color, alpha=1.0, grad=None):
    """Fill an ellipse; grad=(top_color, bottom_color) overrides color."""
    x0 = max(0, int(cx - rx))
    x1 = min(W - 1, int(cx + rx) + 1)
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry) + 1)
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem <= 0:
            continue
        dx = rx * math.sqrt(rem)
        xa = max(x0, int(cx - dx))
        xb = min(x1, int(cx + dx))
        if grad is not None:
            t = (y - (cy - ry)) / (2 * ry)
            col = lerp_c(grad[0], grad[1], max(0.0, min(1.0, t)))
        else:
            col = color
        for x in range(xa, xb + 1):
            blend_px(x, y, col[0], col[1], col[2], alpha)


def fill_circle(cx, cy, r, color, alpha=1.0, grad=None):
    fill_ellipse(cx, cy, r, r, color, alpha, grad)


def disc(cx, cy, r, color, alpha=1.0):
    fill_circle(cx, cy, r, color, alpha)


def thick_line(x0, y0, x1, y1, width, color, alpha=1.0):
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.2) + 1
    rad = width / 2.0
    for s in range(steps + 1):
        t = s / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        fill_circle(x, y, rad, color, alpha)


def wavy_strand(x0, y0, x1, y1, amp, freq, phase, width, color, alpha=1.0):
    """A noodle strand: sine wave between two points."""
    steps = 90
    prev = None
    for s in range(steps + 1):
        t = s / steps
        bx = x0 + (x1 - x0) * t
        by = y0 + (y1 - y0) * t
        nx = bx + math.sin(t * freq * math.pi * 2 + phase) * amp * math.sin(t * math.pi)
        ny = by + math.cos(t * freq * math.pi * 2 + phase) * amp * 0.35 * math.sin(t * math.pi)
        if prev is not None:
            thick_line(prev[0], prev[1], nx, ny, width, color, alpha)
        prev = (nx, ny)


def in_ellipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


# ---------------------------------------------------------------- background
# Warm dark wooden table: vertical gradient + plank bands + grain streaks.
for y in range(H):
    t = y / H
    base = lerp_c((46, 28, 17), (86, 54, 32), t)
    # soft warm glow behind the bowl
    glow = math.exp(-(((y - 1150) / 900.0) ** 2)) * 0.35
    r = int(base[0] + 40 * glow)
    g = int(base[1] + 22 * glow)
    b = int(base[2] + 8 * glow)
    # plank separators
    if (y // 340) % 2 == 0:
        r = max(0, r - 6)
        g = max(0, g - 4)
        b = max(0, b - 3)
    row = y * W * 3
    for x in range(W):
        # subtle horizontal wood grain
        grain = math.sin((x * 0.004) + math.sin(y * 0.011) * 2.2) * 2
        buf[row + x * 3] = max(0, min(255, int(r + grain)))
        buf[row + x * 3 + 1] = max(0, min(255, int(g + grain * 0.7)))
        buf[row + x * 3 + 2] = max(0, min(255, int(b + grain * 0.5)))
# plank seams
for py in (340, 680, 1020, 1360, 1700):
    for x in range(W):
        blend_px(x, py, 20, 12, 7, 0.55)
        blend_px(x, py + 1, 20, 12, 7, 0.35)

# soft shadow under the bowl
fill_ellipse(1024, 1560, 760, 150, (12, 7, 4), alpha=0.5)
fill_ellipse(1024, 1540, 640, 120, (12, 7, 4), alpha=0.35)

# ---------------------------------------------------------------- bowl
# Bowl body: deep red lacquer with a dark rim foot.
fill_ellipse(1024, 1180, 760, 380, (0, 0, 0), alpha=0.0)  # noop guard
fill_ellipse(1024, 1240, 740, 360, (0, 0, 0), alpha=0.0)
# body (lower half of a big ellipse, drawn as full ellipse then broth covers top)
fill_ellipse(1024, 1180, 750, 400, (0, 0, 0), alpha=0.0)
# Draw bowl body via scanline: ellipse centred below the rim.
fill_ellipse(1024, 1330, 745, 330, (0, 0, 0), alpha=0.0)
# Real body: use gradient ellipse centred at (1024, 1150) rx 745 ry 430
fill_ellipse(1024, 1150, 745, 430, (0, 0, 0), alpha=0.0)
# -- actual body fill (red lacquer, darker toward bottom)
fill_ellipse(1024, 1180, 748, 400, (168, 44, 34), alpha=1.0,
             grad=((178, 52, 38), (96, 22, 18)))
# foot ring (small, tucked under the bowl)
fill_ellipse(1024, 1525, 240, 52, (64, 14, 10), alpha=1.0)
fill_ellipse(1024, 1512, 205, 42, (100, 24, 18), alpha=1.0)
# rim highlight (top edge of bowl)
for a in range(0, 360, 2):
    th = math.radians(a)
    x = 1024 + math.cos(th) * 745
    y = 1180 + math.sin(th) * 400
    if y < 1180:
        blend_px(int(x), int(y), 220, 90, 70, 0.25)

# Broth surface (inside the rim)
BROTH = (1024, 1150, 690, 250)
fill_ellipse(*BROTH, (198, 118, 38), alpha=1.0,
             grad=((226, 158, 62), (168, 92, 28)))
# broth inner shadow near rim
for a in range(0, 360):
    th = math.radians(a)
    x = 1024 + math.cos(th) * 660
    y = 1150 + math.sin(th) * 235
    disc(x, y, 26, (140, 70, 18), alpha=0.25)

# chili-oil sheen: glossy red-orange pools on the broth
for (ox, oy, orad) in [(760, 1050, 120), (1250, 1300, 150), (1050, 980, 80),
                       (1400, 1080, 90), (700, 1300, 100)]:
    fill_ellipse(ox, oy, orad, orad * 0.55, (214, 74, 22), alpha=0.45)
    fill_ellipse(ox - orad * 0.25, oy - orad * 0.18, orad * 0.55, orad * 0.3,
                 (240, 120, 40), alpha=0.35)

# ---------------------------------------------------------------- noodles in broth
# Wavy noodle strands clipped to the broth ellipse.
NOODLE = (238, 192, 96)
NOODLE_D = (206, 152, 58)
for i in range(46):
    # random start/end inside broth
    while True:
        sx = rng.uniform(1024 - 620, 1024 + 620)
        sy = rng.uniform(1150 - 200, 1150 + 200)
        if in_ellipse(sx, sy, 1024, 1150, 650, 225):
            break
    ex = sx + rng.uniform(-260, 260)
    ey = sy + rng.uniform(-70, 70)
    if not in_ellipse(ex, ey, 1024, 1150, 650, 225):
        ex, ey = sx, sy
    col = NOODLE if i % 3 else NOODLE_D
    wavy_strand(sx, sy, ex, ey, rng.uniform(14, 34), rng.uniform(1.5, 3.5),
                rng.uniform(0, 6.28), rng.uniform(13, 20), col, alpha=0.95)
# noodle gloss highlights (subtle, thin)
for i in range(12):
    sx = rng.uniform(1024 - 560, 1024 + 560)
    sy = rng.uniform(1150 - 180, 1150 + 180)
    if in_ellipse(sx, sy, 1024, 1150, 620, 210):
        thick_line(sx, sy, sx + rng.uniform(60, 160), sy + rng.uniform(-14, 14),
                   4, (255, 220, 150), alpha=0.3)

# ---------------------------------------------------------------- chashu
def chashu(cx, cy, r):
    fill_circle(cx, cy, r, (196, 110, 92), alpha=1.0)
    fill_circle(cx, cy, r * 0.78, (214, 138, 112), alpha=1.0)
    fill_circle(cx, cy, r * 0.55, (226, 168, 138), alpha=1.0)
    # seared edge + fat ring
    for a in range(0, 360, 3):
        th = math.radians(a)
        x = cx + math.cos(th) * r * 0.9
        y = cy + math.sin(th) * r * 0.9
        disc(x, y, 7, (150, 70, 55), alpha=0.5)
    fill_ellipse(cx - r * 0.3, cy - r * 0.35, r * 0.4, r * 0.22,
                 (255, 210, 180), alpha=0.35)


chashu(760, 1080, 150)
chashu(660, 1280, 130)

# ---------------------------------------------------------------- egg (halved, jammy yolk)
EX, EY = 1380, 1060
fill_ellipse(EX, EY, 150, 185, (246, 240, 224), alpha=1.0,
             grad=((252, 247, 234), (228, 218, 196)))
fill_ellipse(EX, EY, 118, 152, (240, 232, 214), alpha=1.0)
# jammy orange yolk
fill_circle(EX, EY + 10, 92, (238, 128, 26), alpha=1.0,
            grad=((248, 158, 48), (214, 96, 14)))
fill_circle(EX, EY + 10, 62, (246, 152, 40), alpha=1.0)
fill_ellipse(EX - 28, EY - 28, 34, 20, (255, 200, 110), alpha=0.55)
# egg white edge shading
for a in range(0, 360, 4):
    th = math.radians(a)
    x = EX + math.cos(th) * 142
    y = EY + math.sin(th) * 177
    disc(x, y, 8, (200, 188, 164), alpha=0.4)

# ---------------------------------------------------------------- scallions
for i in range(60):
    while True:
        sx = rng.uniform(1024 - 620, 1024 + 620)
        sy = rng.uniform(1150 - 200, 1150 + 200)
        if in_ellipse(sx, sy, 1024, 1150, 640, 215):
            break
    # avoid drawing over the egg centre
    if math.hypot(sx - EX, (sy - EY) * 1.2) < 150:
        continue
    rr = rng.uniform(9, 16)
    g = rng.choice([(52, 150, 74), (70, 175, 90), (38, 128, 62)])
    fill_circle(sx, sy, rr, g, alpha=0.95)
    fill_circle(sx, sy, rr * 0.5, (140, 210, 120), alpha=0.8)

# sesame seeds
for i in range(40):
    sx = rng.uniform(1024 - 600, 1024 + 600)
    sy = rng.uniform(1150 - 190, 1150 + 190)
    if in_ellipse(sx, sy, 1024, 1150, 630, 210):
        fill_ellipse(sx, sy, 9, 5, (245, 228, 190), alpha=0.9)

# ---------------------------------------------------------------- chopsticks + lifted noodles
# Two chopsticks from upper right, tips pinching noodles above the broth.
thick_line(1560, 300, 1150, 1080, 26, (122, 74, 38), alpha=1.0)
thick_line(1620, 360, 1210, 1100, 26, (104, 60, 30), alpha=1.0)
# chopstick highlight
thick_line(1552, 312, 1150, 1060, 7, (190, 130, 80), alpha=0.6)
thick_line(1612, 372, 1210, 1080, 7, (170, 112, 66), alpha=0.6)
# lifted noodle bundle hanging from the tips, glossy and springy
for i in range(9):
    ox = 1150 + i * 16 - 60
    wavy_strand(ox, 1070, ox + rng.uniform(-30, 30), 1330 + rng.uniform(0, 60),
                rng.uniform(10, 22), rng.uniform(2.0, 3.0),
                rng.uniform(0, 6.28), 15,
                NOODLE if i % 2 else NOODLE_D, alpha=0.98)
# noodle clump pinched at the tips
fill_ellipse(1180, 1080, 70, 38, (240, 196, 100), alpha=1.0)
for i in range(6):
    thick_line(1120 + i * 22, 1050, 1120 + i * 22 + rng.uniform(-14, 14), 1120,
               12, NOODLE_D, alpha=0.9)

# ---------------------------------------------------------------- steam
def steam_wisp(x0, y_top, y_bot, strength):
    # Smooth, translucent wisp: many small overlapping ellipses so no
    # banding steps show; alpha fades in and out along the rise.
    steps = 160
    for s in range(steps):
        t = s / steps
        y = y_bot + (y_top - y_bot) * t
        x = x0 + math.sin(t * 7.0 + x0 * 0.01) * (20 + t * 55) + math.sin(t * 19.0) * 8
        rad = 20 + t * 52
        a = strength * (math.sin(t * math.pi) ** 1.5) * 0.42
        fill_ellipse(x, y, rad, rad * 1.9, (255, 244, 228), alpha=a)
    # faint wide halo pass for softness
    for s in range(0, steps, 2):
        t = s / steps
        y = y_bot + (y_top - y_bot) * t
        x = x0 + math.sin(t * 7.0 + x0 * 0.01) * (20 + t * 55)
        rad = 34 + t * 80
        a = strength * (math.sin(t * math.pi) ** 1.5) * 0.16
        fill_ellipse(x, y, rad, rad * 1.8, (255, 240, 222), alpha=a)


steam_wisp(820, 180, 980, 0.13)
steam_wisp(1024, 120, 960, 0.16)
steam_wisp(1240, 200, 980, 0.12)
steam_wisp(920, 260, 1000, 0.09)

# broth gloss: big soft highlight arc on the broth
fill_ellipse(900, 1010, 260, 90, (255, 214, 140), alpha=0.22)
fill_ellipse(1350, 1290, 200, 70, (255, 200, 120), alpha=0.14)

# ---------------------------------------------------------------- downsample 2x -> 1024
out = bytearray(OUT_W * OUT_H * 3)
for y in range(OUT_H):
    for x in range(OUT_W):
        sx = x * 2
        sy = y * 2
        oi = (y * OUT_W + x) * 3
        for c in range(3):
            s = (buf[(sy * W + sx) * 3 + c] + buf[(sy * W + sx + 1) * 3 + c]
                 + buf[((sy + 1) * W + sx) * 3 + c]
                 + buf[((sy + 1) * W + sx + 1) * 3 + c])
            out[oi + c] = s // 4

# vignette only at final resolution (no per-pixel grain: random grain
# inflates the PNG past the 1 MB cap; smooth gradients compress far better)
cx0, cy0 = OUT_W / 2, OUT_H / 2
for y in range(OUT_H):
    for x in range(OUT_W):
        i = (y * OUT_W + x) * 3
        dx = (x - cx0) / cx0
        dy = (y - cy0) / cy0
        d2 = dx * dx + dy * dy
        vig = 1.0 - 0.42 * max(0.0, d2 - 0.55) ** 1.2
        vig = max(0.45, min(1.0, vig))
        for c in range(3):
            out[i + c] = int(out[i + c] * vig)

# ---------------------------------------------------------------- PNG encode
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


ihdr = struct.pack(">IIBBBBB", OUT_W, OUT_H, 8, 2, 0, 0, 0)
raw = bytearray()
for y in range(OUT_H):
    raw.append(0)  # filter none
    raw += out[y * OUT_W * 3:(y + 1) * OUT_W * 3]
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", ihdr)
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "wb") as f:
    f.write(png)
print(f"wrote {OUT_PATH} {len(png)} bytes")

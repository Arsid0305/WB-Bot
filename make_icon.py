"""Generates ReviewBot.ico — run once automatically by ReviewBot.bat."""
import math, os, struct, zlib

def star_polygon(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(n * 2):
        angle = math.pi * i / n - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts

def draw_star(pixels, size, cx, cy, r_out, r_in, color):
    pts = star_polygon(cx, cy, r_out, r_in)
    for y in range(size):
        for x in range(size):
            if point_in_polygon(x + 0.5, y + 0.5, pts):
                pixels[y][x] = color

def point_in_polygon(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def rounded_rect_mask(size, radius):
    mask = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            dx = min(x, size - 1 - x)
            dy = min(y, size - 1 - y)
            if dx >= radius or dy >= radius:
                mask[y][x] = True
            else:
                dist = math.sqrt((dx - radius) ** 2 + (dy - radius) ** 2)
                mask[y][x] = dist <= radius
    return mask

def make_image(size):
    bg   = (124, 58, 237, 255)   # #7C3AED purple
    star = (255, 255, 255, 255)  # white
    transp = (0, 0, 0, 0)

    radius = max(2, size // 6)
    cx, cy = size / 2, size / 2
    r_out  = size * 0.40
    r_in   = size * 0.18

    mask   = rounded_rect_mask(size, radius)
    pixels = [[transp] * size for _ in range(size)]

    for y in range(size):
        for x in range(size):
            if mask[y][x]:
                pixels[y][x] = bg

    draw_star(pixels, size, cx, cy, r_out, r_in, star)
    return pixels

def pixels_to_png(pixels, size):
    def pack_row(row):
        raw = b'\x00'
        for r, g, b, a in row:
            raw += bytes([r, g, b, a])
        return raw

    raw_data = b''.join(pack_row(pixels[y]) for y in range(size))
    compressed = zlib.compress(raw_data)

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return c + struct.pack('>I', crc)

    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    idat_data = compressed

    png  = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr_data)
    png += chunk(b'IDAT', idat_data)
    png += chunk(b'IEND', b'')
    return png

def make_ico(path):
    sizes = [16, 32, 48]
    images = [(s, pixels_to_png(make_image(s), s)) for s in sizes]

    # ICO header
    header = struct.pack('<HHH', 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b''
    for s, data in images:
        entries += struct.pack('<BBBBHHII', s, s, 0, 0, 1, 32, len(data), offset)
        offset += len(data)

    with open(path, 'wb') as f:
        f.write(header + entries)
        for _, data in images:
            f.write(data)

    print(f"  Created: {path}")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    make_ico(os.path.join(here, "ReviewBot.ico"))

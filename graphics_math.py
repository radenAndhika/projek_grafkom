"""
graphics_math.py
Modul algoritma grafika inti untuk Mini Paint & Draw Studio.
Berisi: DDA, Bresenham, Bezier, Flood Fill, dan Transformasi 2D.
"""

import math


# ─────────────────────────────────────────────
#  ALGORITMA GARIS
# ─────────────────────────────────────────────

def dda_line(x0, y0, x1, y1):
    """
    Algoritma DDA (Digital Differential Analyzer) untuk menggambar garis.
    Mengembalikan list of (x, y) piksel yang perlu diwarnai.
    """
    points = []
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [(x0, y0)]
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = float(x0), float(y0)
    for _ in range(int(steps) + 1):
        points.append((round(x), round(y)))
        x += x_inc
        y += y_inc
    return points


def bresenham_line(x0, y0, x1, y1):
    """
    Algoritma Bresenham untuk menggambar garis – lebih efisien daripada DDA.
    Hanya menggunakan operasi integer.
    Mengembalikan list of (x, y) piksel.
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points


# ─────────────────────────────────────────────
#  KURVA BEZIER
# ─────────────────────────────────────────────

def bezier_curve(control_points, num_steps=200):
    """
    Menghitung titik-titik di sepanjang kurva Bezier (de Casteljau algorithm).
    control_points: list of (x, y) tuples
    Mengembalikan list of (x, y) titik sepanjang kurva.
    """
    def de_casteljau(points, t):
        while len(points) > 1:
            points = [
                (
                    (1 - t) * points[i][0] + t * points[i + 1][0],
                    (1 - t) * points[i][1] + t * points[i + 1][1]
                )
                for i in range(len(points) - 1)
            ]
        return points[0]

    curve_points = []
    for i in range(num_steps + 1):
        t = i / num_steps
        pt = de_casteljau(list(control_points), t)
        curve_points.append((int(pt[0]), int(pt[1])))
    return curve_points


# ─────────────────────────────────────────────
#  FLOOD FILL
# ─────────────────────────────────────────────

def flood_fill(surface, x, y, fill_color):
    """
    Algoritma Flood Fill menggunakan stack (iterative) untuk mewarnai area.
    surface: pygame.Surface
    x, y: titik awal fill
    fill_color: tuple (R, G, B)
    Mengembalikan set of (x, y) piksel yang berhasil di-fill.
    """
    import pygame
    width, height = surface.get_size()
    target_color = surface.get_at((x, y))[:3]
    fill_color_3 = fill_color[:3]

    if target_color == fill_color_3:
        return set()  # Warna sudah sama, tidak perlu fill

    stack = [(x, y)]
    visited = set()

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        if cx < 0 or cx >= width or cy < 0 or cy >= height:
            continue
        current = surface.get_at((cx, cy))[:3]
        if current != target_color:
            continue
        visited.add((cx, cy))
        surface.set_at((cx, cy), fill_color_3)
        stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

    return visited


# ─────────────────────────────────────────────
#  TRANSFORMASI 2D (Matriks)
# ─────────────────────────────────────────────

def translate_points(points, tx, ty):
    """Translasi: Menggeser sekumpulan titik sebesar (tx, ty)."""
    return [(x + tx, y + ty) for x, y in points]


def rotate_points(points, angle_deg, cx=0, cy=0):
    """
    Rotasi: Memutar sekumpulan titik sebesar angle_deg derajat
    di sekitar titik pusat (cx, cy).
    """
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    rotated = []
    for x, y in points:
        # Translasi ke origin
        dx, dy = x - cx, y - cy
        # Rotasi
        nx = cos_a * dx - sin_a * dy
        ny = sin_a * dx + cos_a * dy
        # Translasi kembali
        rotated.append((nx + cx, ny + cy))
    return rotated


def scale_points(points, sx, sy, cx=0, cy=0):
    """
    Scaling: Memperbesar/memperkecil sekumpulan titik
    relatif terhadap titik pusat (cx, cy).
    """
    scaled = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        scaled.append((dx * sx + cx, dy * sy + cy))
    return scaled


def get_centroid(points):
    """Menghitung titik pusat (centroid) dari sekumpulan titik."""
    if not points:
        return (0, 0)
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return (cx, cy)

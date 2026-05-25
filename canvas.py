"""
canvas.py
Modul yang mengelola kanvas gambar dan semua objek (shapes) di atasnya.
"""

import pygame
import math
import copy
from collections import deque
from graphics_math import (
    translate_points, rotate_points, scale_points, get_centroid
)


class Shape:
    """
    Representasi objek bentuk (shape) yang bisa ditransformasi.
    Mendukung: rectangle, circle, triangle, freehand (polygon)
    """

    def __init__(self, shape_type, points, color=(255, 0, 0),
                 thickness=2, filled=False, fill_color=None):
        self.shape_type = shape_type   # 'rect', 'circle', 'triangle', 'polygon'
        self.points = [list(p) for p in points]  # list of [x, y]
        self.color = color
        self.thickness = thickness
        self.filled = filled
        self.fill_color = fill_color   # Warna isi (None = gunakan self.color)
        self.selected = False

        # Untuk animasi bouncing
        self.vx = 0.0
        self.vy = 0.0
        self.angular_vel = 0.0  # derajat per frame

    def get_centroid(self):
        pts = [(p[0], p[1]) for p in self.points]
        return get_centroid(pts)

    def translate(self, tx, ty):
        pts = [(p[0], p[1]) for p in self.points]
        moved = translate_points(pts, tx, ty)
        self.points = [list(p) for p in moved]

    def rotate(self, angle_deg):
        cx, cy = self.get_centroid()
        pts = [(p[0], p[1]) for p in self.points]
        rotated = rotate_points(pts, angle_deg, cx, cy)
        self.points = [list(p) for p in rotated]

    def scale(self, sx, sy):
        cx, cy = self.get_centroid()
        pts = [(p[0], p[1]) for p in self.points]
        scaled = scale_points(pts, sx, sy, cx, cy)
        self.points = [list(p) for p in scaled]

    def get_bounding_box(self):
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def contains_point(self, mx, my):
        """Cek apakah koordinat mouse (mx, my) ada di dalam bounding box shape."""
        bx, by, bw, bh = self.get_bounding_box()
        margin = 10
        return (bx - margin <= mx <= bx + bw + margin and
                by - margin <= my <= by + bh + margin)

    def hit_test(self, mx, my):
        """Cek apakah titik (mx, my) ada di DALAM shape (presisi per shape type)."""
        pts = [(int(p[0]), int(p[1])) for p in self.points]

        if self.shape_type == 'rect' and len(pts) == 2:
            x0, y0 = pts[0]
            x1, y1 = pts[1]
            return min(x0, x1) <= mx <= max(x0, x1) and min(y0, y1) <= my <= max(y0, y1)

        elif self.shape_type == 'circle' and len(pts) == 2:
            cx, cy = pts[0]
            rx, ry = pts[1]
            radius = math.hypot(rx - cx, ry - cy)
            return math.hypot(mx - cx, my - cy) <= radius

        elif self.shape_type in ('triangle', 'polygon') and len(pts) >= 3:
            # Ray casting algorithm
            n = len(pts)
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if ((yi > my) != (yj > my)) and (
                        mx < (xj - xi) * (my - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
            return inside

        return False

    def draw(self, surface):
        pts_int = [(int(p[0]), int(p[1])) for p in self.points]
        # Warna isi: pakai fill_color jika ada, fallback ke color
        fc = self.fill_color if self.fill_color is not None else self.color

        if self.selected:
            # Gambar outline seleksi
            bx, by, bw, bh = self.get_bounding_box()
            sel_rect = pygame.Rect(bx - 5, by - 5, bw + 10, bh + 10)
            pygame.draw.rect(surface, (0, 180, 255), sel_rect, 2)

        if self.shape_type == 'polygon' and len(pts_int) >= 2:
            if len(pts_int) >= 3 and self.filled:
                pygame.draw.polygon(surface, fc, pts_int)
                pygame.draw.polygon(surface, self.color, pts_int, self.thickness)
            elif len(pts_int) >= 3:
                pygame.draw.polygon(surface, self.color, pts_int, self.thickness)
            else:
                pygame.draw.lines(surface, self.color, False, pts_int, self.thickness)

        elif self.shape_type == 'rect' and len(pts_int) == 2:
            x0, y0 = pts_int[0]
            x1, y1 = pts_int[1]
            rect = pygame.Rect(min(x0, x1), min(y0, y1),
                               abs(x1 - x0), abs(y1 - y0))
            if self.filled:
                pygame.draw.rect(surface, fc, rect)
            pygame.draw.rect(surface, self.color, rect, self.thickness)

        elif self.shape_type == 'circle' and len(pts_int) == 2:
            cx, cy = pts_int[0]
            rx, ry = pts_int[1]
            radius = int(math.hypot(rx - cx, ry - cy))
            if radius > 0:
                if self.filled:
                    pygame.draw.circle(surface, fc, (cx, cy), radius)
                pygame.draw.circle(surface, self.color, (cx, cy), radius,
                                   self.thickness)

        elif self.shape_type == 'triangle' and len(pts_int) == 3:
            if self.filled:
                pygame.draw.polygon(surface, fc, pts_int)
            pygame.draw.polygon(surface, self.color, pts_int, self.thickness)

        elif self.shape_type == 'line_segment' and len(pts_int) == 2:
            pygame.draw.line(surface, self.color, pts_int[0], pts_int[1],
                             self.thickness)


class Canvas:
    """
    Kanvas utama aplikasi. Menyimpan:
    - Surface piksel (untuk drawing mode)
    - List Shape objek (untuk shape mode)
    """

    def __init__(self, width, height, bg_color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.bg_color = bg_color

        # Dua layer: pixel layer dan shape layer
        self.pixel_surface = pygame.Surface((width, height))
        self.pixel_surface.fill(bg_color)

        self.shapes = []
        self.selected_shape = None

        # Animasi
        self.animating = False

        # Undo / Redo stacks (masing-masing menyimpan max 30 snapshot)
        self._undo_stack: deque = deque(maxlen=30)
        self._redo_stack: deque = deque(maxlen=30)
        # Simpan state awal (kanvas kosong)
        self.save_state()

    # ── UNDO / REDO ──────────────────────────────────────────

    def save_state(self):
        """
        Simpan snapshot state kanvas saat ini ke undo stack.
        Dipanggil setiap kali aksi menggambar selesai.
        """
        snapshot = {
            'pixel': self.pixel_surface.copy(),
            'shapes': copy.deepcopy(self.shapes),
        }
        self._undo_stack.append(snapshot)
        # Setiap aksi baru menghapus redo history
        self._redo_stack.clear()

    def undo(self):
        """
        Kembalikan kanvas ke state sebelumnya.
        State saat ini disimpan ke redo stack.
        """
        # Harus ada minimal 2 snapshot (state awal + 1 aksi)
        if len(self._undo_stack) <= 1:
            return  # Tidak ada yang bisa di-undo
        # Pindahkan state saat ini ke redo stack
        current = self._undo_stack.pop()
        self._redo_stack.append(current)
        # Restore snapshot sebelumnya
        prev = self._undo_stack[-1]
        self.pixel_surface.blit(prev['pixel'], (0, 0))
        self.shapes = copy.deepcopy(prev['shapes'])
        self.selected_shape = None

    def redo(self):
        """
        Ulangi aksi yang sudah di-undo.
        """
        if not self._redo_stack:
            return  # Tidak ada yang bisa di-redo
        # Pindahkan state redo ke undo stack
        next_state = self._redo_stack.pop()
        self._undo_stack.append(next_state)
        # Restore snapshot tersebut
        self.pixel_surface.blit(next_state['pixel'], (0, 0))
        self.shapes = copy.deepcopy(next_state['shapes'])
        self.selected_shape = None

    @property
    def can_undo(self):
        return len(self._undo_stack) > 1

    @property
    def can_redo(self):
        return len(self._redo_stack) > 0

    # ── CANVAS OPERATIONS ────────────────────────────────────

    def clear(self):
        self.save_state()  # Simpan state sebelum dihapus
        self.pixel_surface.fill(self.bg_color)
        self.shapes.clear()
        self.selected_shape = None
        self.save_state()  # Simpan state kosong sebagai undo point

    def add_shape(self, shape):
        self.shapes.append(shape)

    def select_shape_at(self, mx, my):
        """Pilih shape yang diklik. Urutan: shape paling atas (index terakhir) diprioritaskan."""
        self.selected_shape = None
        for shape in reversed(self.shapes):
            shape.selected = False
        for shape in reversed(self.shapes):
            if shape.contains_point(mx, my):
                shape.selected = True
                self.selected_shape = shape
                return shape
        return None

    def deselect_all(self):
        for shape in self.shapes:
            shape.selected = False
        self.selected_shape = None

    def update_animation(self, canvas_rect):
        """Update posisi semua shape saat mode animasi aktif."""
        if not self.animating:
            return
        for shape in self.shapes:
            if shape.vx == 0 and shape.vy == 0:
                import random
                shape.vx = random.uniform(-3, 3) or 2
                shape.vy = random.uniform(-3, 3) or 2
                shape.angular_vel = random.uniform(-3, 3)

            # Gerakkan
            shape.translate(shape.vx, shape.vy)
            # Rotasi dinamis
            if shape.shape_type not in ('rect', 'circle'):
                shape.rotate(shape.angular_vel)

            # Bounce dari dinding
            bx, by, bw, bh = shape.get_bounding_box()
            if bx < canvas_rect.left or bx + bw > canvas_rect.right:
                shape.vx *= -1
                shape.translate(shape.vx * 2, 0)
            if by < canvas_rect.top or by + bh > canvas_rect.bottom:
                shape.vy *= -1
                shape.translate(0, shape.vy * 2)

    def draw(self, surface, offset_x=0, offset_y=0):
        """Render kanvas (pixel layer + shapes) ke surface utama."""
        surface.blit(self.pixel_surface, (offset_x, offset_y))
        for shape in self.shapes:
            # Buat surface sementara dengan offset
            temp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            temp.fill((0, 0, 0, 0))
            shape.draw(temp)
            surface.blit(temp, (offset_x, offset_y))

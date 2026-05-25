"""
main.py
File utama aplikasi Mini Paint & Draw Studio.
Menjalankan game loop, mengelola event, dan mengintegrasikan semua modul.

Cara menjalankan:
    python main.py
"""

import pygame
import sys
import math

from graphics_math import (
    bresenham_line, dda_line, bezier_curve, flood_fill
)
from canvas import Canvas, Shape
from ui import (
    UI, SIDEBAR_WIDTH, TOOLBAR_HEIGHT,
    DARK_BG, PANEL_BG, PANEL_BORDER, ACCENT, TEXT_COLOR, TEXT_DIM, WHITE
)

# ─────────────────────────────────────────────
#  KONFIGURASI WINDOW
# ─────────────────────────────────────────────
SCREEN_W  = 1280
SCREEN_H  = 760
FPS       = 60
APP_TITLE = 'Mini Paint & Draw Studio – Grafika Komputer'


# ─────────────────────────────────────────────
#  HELPER: Menggambar piksel dari list titik ke surface
# ─────────────────────────────────────────────

def draw_pixels(surface, points, color, thickness=1, dashed=False):
    """Gambar sekumpulan piksel/titik ke surface."""
    if dashed:
        # Gambar selang-seling (setiap 2 titik digambar, 2 dilewati)
        for i, (x, y) in enumerate(points):
            if i % 4 < 2:
                if thickness == 1:
                    surface.set_at((x, y), color)
                else:
                    pygame.draw.circle(surface, color, (x, y), thickness // 2)
    else:
        for x, y in points:
            if thickness == 1:
                surface.set_at((x, y), color)
            else:
                pygame.draw.circle(surface, color, (x, y), thickness // 2)


def make_triangle_points(cx, cy, size=60):
    """Membuat titik-titik segitiga sama sisi dari centroid."""
    h = int(size * math.sqrt(3) / 2)
    return [
        (cx,          cy - size // 2 - 10),
        (cx - size,   cy + h - 10),
        (cx + size,   cy + h - 10),
    ]


# ─────────────────────────────────────────────
#  KELAS APLIKASI UTAMA
# ─────────────────────────────────────────────

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(APP_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()

        # Inisialisasi modul
        canvas_w = SCREEN_W - SIDEBAR_WIDTH
        canvas_h = SCREEN_H - TOOLBAR_HEIGHT
        self.canvas = Canvas(canvas_w, canvas_h, bg_color=(250, 250, 255))
        self.ui = UI(SCREEN_W, SCREEN_H)

        # State drawing
        self.drawing        = False
        self.start_pos      = None      # Koordinat awal di kanvas
        self.preview_points = []        # Titik preview saat menggambar garis/kurva
        self.bezier_cps     = []        # Titik kontrol Bezier
        self.freehand_pts   = []        # Titik freehand pencil

        # State select/transform
        self.dragging_shape  = False
        self.drag_offset     = (0, 0)
        self.last_mouse_pos  = None

        # State eraser
        self.eraser_last_pos = None     # Posisi eraser sebelumnya (untuk interpolasi)

        # State teks
        self.text_input_active = False
        self.text_buffer       = ''
        self.text_pos          = (0, 0)

        # Font untuk teks di kanvas
        self.canvas_font = pygame.font.SysFont('segoeui', 24, bold=True)

    # ── EVENT HANDLING ──────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Input teks
            if self.text_input_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self._finish_text()
                    elif event.key == pygame.K_BACKSPACE:
                        self.text_buffer = self.text_buffer[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.text_input_active = False
                        self.text_buffer = ''
                    else:
                        self.text_buffer += event.unicode
                continue  # Jangan proses event lain saat mengetik

            # UI events
            action = self.ui.handle_event(event)
            if action.get('clear'):
                self.canvas.clear()
            if action.get('undo'):
                self.canvas.undo()
            if action.get('redo'):
                self.canvas.redo()
            if 'animate' in action:
                self.canvas.animating = action['animate']
                if not action['animate']:
                    for shape in self.canvas.shapes:
                        shape.vx = shape.vy = shape.angular_vel = 0

            # Transformasi keyboard saat ada shape terseleksi
            if event.type == pygame.KEYDOWN:
                self._handle_keyboard(event)

            # Mouse events untuk kanvas
            if self.ui.is_on_canvas(event.pos if hasattr(event, 'pos') else (0, 0)):
                self._handle_canvas_event(event)

    def _handle_keyboard(self, event):
        sel = self.canvas.selected_shape

        # ── Ctrl+Z = Undo, Ctrl+Y / Ctrl+Shift+Z = Redo ──
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            if event.key == pygame.K_z and not (mods & pygame.KMOD_SHIFT):
                self.canvas.undo()
                return
            if event.key == pygame.K_y or (event.key == pygame.K_z and mods & pygame.KMOD_SHIFT):
                self.canvas.redo()
                return

        if event.key == pygame.K_ESCAPE:
            self.canvas.deselect_all()

        if sel:
            # Translasi dengan tombol panah
            step = 5
            if event.key == pygame.K_LEFT:  sel.translate(-step, 0)
            if event.key == pygame.K_RIGHT: sel.translate(step, 0)
            if event.key == pygame.K_UP:    sel.translate(0, -step)
            if event.key == pygame.K_DOWN:  sel.translate(0, step)
            # Rotasi dengan [ dan ]
            if event.key == pygame.K_LEFTBRACKET:  sel.rotate(-15)
            if event.key == pygame.K_RIGHTBRACKET: sel.rotate(15)
            # Scaling dengan + dan -
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS):  sel.scale(1.1, 1.1)
            if event.key == pygame.K_MINUS: sel.scale(0.9, 0.9)
            # Hapus shape – simpan state dulu sebelum dihapus
            if event.key == pygame.K_DELETE:
                self.canvas.save_state()
                if sel in self.canvas.shapes:
                    self.canvas.shapes.remove(sel)
                self.canvas.selected_shape = None
                self.canvas.save_state()

    def _handle_canvas_event(self, event):
        tool = self.ui.active_tool
        color = self.ui.active_color
        thick = self.ui.thickness
        dashed = (self.ui.line_style == 'dashed')
        filled = self.ui.fill_mode

        if not hasattr(event, 'pos'):
            return

        cpos = self.ui.canvas_pos(event.pos)
        cx, cy = cpos

        # ── TOOL: SELECT ──
        if tool == 'select':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shape = self.canvas.select_shape_at(cx, cy)
                if shape:
                    self.dragging_shape = True
                    self.drag_offset = (cx - shape.get_centroid()[0],
                                        cy - shape.get_centroid()[1])
                else:
                    self.dragging_shape = False
            if event.type == pygame.MOUSEBUTTONUP:
                self.dragging_shape = False
            if event.type == pygame.MOUSEMOTION and self.dragging_shape:
                sel = self.canvas.selected_shape
                if sel:
                    tx = cx - self.drag_offset[0] - sel.get_centroid()[0]
                    ty = cy - self.drag_offset[1] - sel.get_centroid()[1]
                    sel.translate(tx, ty)
            return

        # ── TOOL: BUCKET (Flood Fill) ──
        if tool == 'bucket':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                w, h = self.canvas.pixel_surface.get_size()
                if 0 <= cx < w and 0 <= cy < h:
                    self.canvas.save_state()

                    # Prioritas: cek apakah klik mengenai shape vector (terbalik = atas dulu)
                    hit_shape = None
                    for shape in reversed(self.canvas.shapes):
                        if shape.hit_test(cx, cy):
                            hit_shape = shape
                            break

                    if hit_shape:
                        # Fill langsung ke shape object → ikut gerak saat animasi
                        hit_shape.filled = True
                        hit_shape.fill_color = color
                    else:
                        # Tidak ada shape → flood fill pada pixel_surface
                        # Gunakan composite agar batas shape tetap dihormati
                        self._bucket_fill_composite(cx, cy, color)

                    self.canvas.save_state()
            return


        # ── TOOL: TEXT ──
        if tool == 'text':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.text_input_active = True
                self.text_buffer = ''
                self.text_pos = (cx, cy)
            return

        # ── TOOL: ERASER ──
        if tool == 'eraser':
            radius = max(thick, 4)  # ukuran eraser = nilai slider langsung

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Simpan state sebelum mulai menghapus
                self.canvas.save_state()
                self.eraser_last_pos = (cx, cy)
                # Hapus di titik klik pertama
                pygame.draw.circle(self.canvas.pixel_surface,
                                   self.canvas.bg_color, (cx, cy), radius)

            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                # Interpolasi antara posisi terakhir dan posisi sekarang
                if self.eraser_last_pos:
                    lx, ly = self.eraser_last_pos
                    dist = math.hypot(cx - lx, cy - ly)
                    steps = max(1, int(dist / max(1, radius // 2)))
                    for i in range(steps + 1):
                        ix = int(lx + (cx - lx) * i / steps)
                        iy = int(ly + (cy - ly) * i / steps)
                        pygame.draw.circle(self.canvas.pixel_surface,
                                           self.canvas.bg_color, (ix, iy), radius)
                self.eraser_last_pos = (cx, cy)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Simpan snapshot setelah selesai menghapus
                self.canvas.save_state()
                self.eraser_last_pos = None

            return

        # ── TOOL: BEZIER ──
        if tool == 'bezier':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Tambah titik kontrol
                    self.bezier_cps.append((cx, cy))
                elif event.button == 3:
                    # Klik kanan: finalisasi kurva
                    if len(self.bezier_cps) >= 2:
                        self.canvas.save_state()
                        pts = bezier_curve(self.bezier_cps)
                        draw_pixels(self.canvas.pixel_surface, pts, color, thick, dashed)
                        self.canvas.save_state()
                    self.bezier_cps.clear()
            return

        # ── TOOLS LAIN: PENCIL, LINE, RECT, CIRCLE, TRIANGLE ──
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drawing   = True
            self.start_pos = (cx, cy)
            self.freehand_pts = [(cx, cy)]

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drawing:
                self.drawing = False
                ex, ey = cx, cy
                sx, sy = self.start_pos

                if tool == 'pencil':
                    # Freehand selesai – simpan snapshot
                    self.canvas.save_state()

                elif tool == 'line':
                    self.canvas.save_state()
                    pts = bresenham_line(sx, sy, ex, ey)
                    draw_pixels(self.canvas.pixel_surface, pts, color, thick, dashed)
                    self.canvas.save_state()

                elif tool in ('rect', 'circle'):
                    shape = Shape(
                        shape_type=tool,
                        points=[(sx, sy), (ex, ey)],
                        color=color,
                        thickness=thick,
                        filled=filled
                    )
                    self.canvas.add_shape(shape)
                    self.canvas.save_state()

                elif tool == 'triangle':
                    mid_x = (sx + ex) // 2
                    pts = [
                        (mid_x, sy),
                        (sx, ey),
                        (ex, ey)
                    ]
                    shape = Shape(
                        shape_type='triangle',
                        points=pts,
                        color=color,
                        thickness=thick,
                        filled=filled
                    )
                    self.canvas.add_shape(shape)
                    self.canvas.save_state()

        if event.type == pygame.MOUSEMOTION:
            if self.drawing:
                ex, ey = cx, cy
                sx, sy = self.start_pos

                if tool == 'pencil':
                    # Gambar freehand langsung ke pixel surface
                    if self.freehand_pts:
                        lx, ly = self.freehand_pts[-1]
                        pts = bresenham_line(lx, ly, ex, ey)
                        draw_pixels(self.canvas.pixel_surface, pts, color, thick, dashed)
                    self.freehand_pts.append((ex, ey))

                else:
                    # Simpan preview
                    if tool == 'line':
                        self.preview_points = bresenham_line(sx, sy, ex, ey)
                    elif tool == 'rect':
                        self.preview_points = [('rect', sx, sy, ex, ey)]
                    elif tool == 'circle':
                        self.preview_points = [('circle', sx, sy, ex, ey)]
                    elif tool == 'triangle':
                        mid_x = (sx + ex) // 2
                        self.preview_points = [
                            ('triangle', [(mid_x, sy), (sx, ey), (ex, ey)])
                        ]

    def _bucket_fill_composite(self, cx, cy, fill_color):
        """
        Flood fill yang menghormati batas shapes tanpa merusak shapes list.

        Cara kerja:
        1. Buat composite surface sementara = pixel_surface + semua shapes
        2. Jalankan flood fill pada composite → dapat set piksel yang di-fill
        3. Terapkan piksel tersebut ke pixel_surface asli
        4. shapes list TIDAK diubah → animasi tetap berjalan
        """
        w, h = self.canvas.pixel_surface.get_size()

        # Buat composite sementara
        composite = self.canvas.pixel_surface.copy()
        for shape in self.canvas.shapes:
            shape.draw(composite)

        # Flood fill pada composite, dapatkan set piksel yang berubah
        filled_pixels = flood_fill(composite, cx, cy, fill_color)

        # Terapkan hasil fill ke pixel_surface asli
        fill_rgb = fill_color[:3]
        for px, py in filled_pixels:
            self.canvas.pixel_surface.set_at((px, py), fill_rgb)

    def _finish_text(self):
        if self.text_buffer.strip():
            tx, ty = self.text_pos
            text_surf = self.canvas_font.render(
                self.text_buffer, True, self.ui.active_color
            )
            self.canvas.save_state()
            self.canvas.pixel_surface.blit(text_surf, (tx, ty))
            self.canvas.save_state()
        self.text_input_active = False
        self.text_buffer = ''

    # ── RENDER ──────────────────────────────────────────────

    def draw_preview(self):
        """Gambar preview sementara saat menggambar (sebelum mouse dilepas)."""
        if not self.drawing or not self.preview_points:
            return
        surf = self.screen
        offset_x = self.ui.canvas_rect.x
        offset_y = self.ui.canvas_rect.y
        color = self.ui.active_color
        thick = self.ui.thickness

        for item in self.preview_points:
            if isinstance(item, tuple) and isinstance(item[0], str):
                kind = item[0]
                if kind == 'rect':
                    _, sx, sy, ex, ey = item
                    r = pygame.Rect(min(sx, ex) + offset_x,
                                    min(sy, ey) + offset_y,
                                    abs(ex - sx), abs(ey - sy))
                    pygame.draw.rect(surf, color, r, thick)
                elif kind == 'circle':
                    _, sx, sy, ex, ey = item
                    radius = int(math.hypot(ex - sx, ey - sy))
                    if radius > 0:
                        pygame.draw.circle(surf, color,
                                           (sx + offset_x, sy + offset_y),
                                           radius, thick)
                elif kind == 'triangle':
                    _, pts = item
                    shifted = [(x + offset_x, y + offset_y) for x, y in pts]
                    if len(shifted) >= 3:
                        pygame.draw.polygon(surf, color, shifted, thick)
            else:
                # Titik piksel biasa (untuk line preview)
                x, y = item
                pygame.draw.circle(surf, color,
                                   (x + offset_x, y + offset_y),
                                   max(1, thick // 2))

    def draw_bezier_preview(self):
        """Tampilkan titik kontrol Bezier yang sudah diklik."""
        if not self.bezier_cps:
            return
        ox, oy = self.ui.canvas_rect.x, self.ui.canvas_rect.y
        for i, (x, y) in enumerate(self.bezier_cps):
            pygame.draw.circle(self.screen, ACCENT, (x + ox, y + oy), 5)
            if i > 0:
                px, py = self.bezier_cps[i - 1]
                pygame.draw.line(self.screen, (100, 100, 180),
                                 (px + ox, py + oy), (x + ox, y + oy), 1)
        # Preview kurva
        if len(self.bezier_cps) >= 2:
            curve = bezier_curve(self.bezier_cps)
            for i in range(len(curve) - 1):
                x1, y1 = curve[i]
                x2, y2 = curve[i + 1]
                pygame.draw.line(self.screen, self.ui.active_color,
                                 (x1 + ox, y1 + oy), (x2 + ox, y2 + oy), 1)

    def draw_text_cursor(self):
        """Tampilkan teks yang sedang diketik di kanvas."""
        if not self.text_input_active:
            return
        ox, oy = self.ui.canvas_rect.x, self.ui.canvas_rect.y
        tx, ty = self.text_pos
        preview = self.canvas_font.render(
            self.text_buffer + '|', True, self.ui.active_color
        )
        self.screen.blit(preview, (tx + ox, ty + oy))

    def draw_canvas_border(self):
        pygame.draw.rect(self.screen, PANEL_BORDER, self.ui.canvas_rect, 1)

    def draw_eraser_cursor(self):
        """Tampilkan lingkaran preview ukuran eraser saat tool Eraser aktif."""
        if self.ui.active_tool != 'eraser':
            return
        mouse_pos = pygame.mouse.get_pos()
        if not self.ui.is_on_canvas(mouse_pos):
            return
        radius = max(self.ui.thickness, 4)
        # Lingkaran luar putih
        pygame.draw.circle(self.screen, WHITE, mouse_pos, radius + 1, 1)
        # Lingkaran dalam hitam (outline tipis)
        pygame.draw.circle(self.screen, (50, 50, 50), mouse_pos, radius, 1)
        # Crosshair kecil di tengah
        cx, cy = mouse_pos
        pygame.draw.line(self.screen, (100, 100, 100), (cx - 3, cy), (cx + 3, cy), 1)
        pygame.draw.line(self.screen, (100, 100, 100), (cx, cy - 3), (cx, cy + 3), 1)

    def render(self):
        self.screen.fill(DARK_BG)

        # Sync state undo/redo ke UI setiap frame
        self.ui.update_undo_redo_state(
            self.canvas.can_undo,
            self.canvas.can_redo
        )

        # Gambar kanvas
        self.canvas.draw(
            self.screen,
            offset_x=self.ui.canvas_rect.x,
            offset_y=self.ui.canvas_rect.y
        )

        # Preview menggambar
        self.draw_preview()
        self.draw_bezier_preview()
        self.draw_text_cursor()
        self.draw_eraser_cursor()
        self.draw_canvas_border()

        # UI sidebar & toolbar
        self.ui.draw(self.screen)

        pygame.display.flip()

    # ── MAIN LOOP ────────────────────────────────────────────

    def run(self):
        print("=" * 50)
        print("  Mini Paint & Draw Studio")
        print("  Grafika Komputer & Multimedia")
        print("=" * 50)
        print("Controls:")
        print("  [P] Pencil  [L] Line  [B] Bezier (klik kiri=titik, kanan=selesai)")
        print("  [F] Fill    [R] Rect  [C] Circle  [T] Triangle")
        print("  [X] Text    [S] Select  [E] Eraser")
        print("  [Arrow keys] Move shape  [[ / ]] Rotate  [+/-] Scale")
        print("  [Del] Delete selected   [Esc] Deselect")
        print()

        while True:
            self.handle_events()

            # Update animasi shape
            self.canvas.update_animation(
                pygame.Rect(0, 0, self.canvas.width, self.canvas.height)
            )

            self.render()
            self.clock.tick(FPS)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.run()

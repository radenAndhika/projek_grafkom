"""
ui.py
Modul antarmuka pengguna: Toolbar, Sidebar, Palet Warna, dan semua elemen UI.
"""

import pygame


# ─────────────────────────────────────────────
#  WARNA TEMA
# ─────────────────────────────────────────────
DARK_BG       = (18, 18, 28)
PANEL_BG      = (28, 28, 42)
PANEL_BORDER  = (50, 50, 75)
ACCENT        = (100, 140, 255)
ACCENT_HOVER  = (130, 165, 255)
TEXT_COLOR    = (220, 220, 240)
TEXT_DIM      = (130, 130, 160)
WHITE         = (255, 255, 255)
BLACK         = (0, 0, 0)
SELECTED_BG   = (50, 65, 120)


# Palet warna yang tersedia untuk pengguna (24 warna, 6 kolom × 4 baris)
COLOR_PALETTE = [
    # Baris 1: Netral
    (0,   0,   0),    # Hitam
    (60,  60,  60),   # Abu sangat gelap
    (120, 120, 120),  # Abu gelap
    (180, 180, 180),  # Abu terang
    (220, 220, 220),  # Abu sangat terang
    (255, 255, 255),  # Putih
    # Baris 2: Merah – Oranye – Kuning
    (200, 20,  20),   # Merah tua
    (230, 60,  30),   # Merah oranye
    (230, 120, 20),   # Oranye
    (240, 190, 20),   # Kuning
    (180, 220, 20),   # Kuning hijau
    (80,  180, 20),   # Hijau muda
    # Baris 3: Hijau – Biru
    (20,  150, 60),   # Hijau
    (20,  160, 130),  # Teal
    (20,  200, 210),  # Cyan
    (20,  130, 230),  # Biru muda
    (40,  70,  220),  # Biru
    (70,  20,  200),  # Indigo
    # Baris 4: Ungu – Pink – Coklat
    (150, 20,  200),  # Ungu
    (210, 20,  140),  # Magenta
    (230, 70,  130),  # Pink
    (240, 140, 160),  # Pink muda
    (160, 90,  40),   # Coklat
    (210, 160, 110),  # Krem
]

# Konstanta layout palet
PALETTE_COLS     = 6
SWATCH_SIZE      = 22
SWATCH_GAP       = 2
PALETTE_START_Y  = 55

# Definisi semua tools
TOOLS = [
    {'id': 'pencil',    'label': '✏️', 'name': 'Pencil',    'shortcut': 'P'},
    {'id': 'line',      'label': '╱',  'name': 'Line',      'shortcut': 'L'},
    {'id': 'bezier',    'label': '〜',  'name': 'Bezier',   'shortcut': 'B'},
    {'id': 'bucket',    'label': '🪣', 'name': 'Fill',      'shortcut': 'F'},
    {'id': 'rect',      'label': '▭',  'name': 'Rectangle', 'shortcut': 'R'},
    {'id': 'circle',    'label': '○',  'name': 'Circle',    'shortcut': 'C'},
    {'id': 'triangle',  'label': '△',  'name': 'Triangle',  'shortcut': 'T'},
    {'id': 'text',      'label': 'A',  'name': 'Text',      'shortcut': 'X'},
    {'id': 'select',    'label': '↖',  'name': 'Select',    'shortcut': 'S'},
    {'id': 'eraser',    'label': '⌫',  'name': 'Eraser',    'shortcut': 'E'},
]

SIDEBAR_WIDTH  = 220
TOOLBAR_HEIGHT = 60


class Button:
    def __init__(self, rect, label, tooltip='', icon=None,
                 bg=PANEL_BG, hover_bg=SELECTED_BG, text_color=TEXT_COLOR,
                 font=None, border_radius=10, border_color=PANEL_BORDER):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.tooltip = tooltip
        self.icon = icon
        self.bg = bg
        self.hover_bg = hover_bg
        self.text_color = text_color
        self.font = font
        self.border_radius = border_radius
        self.border_color = border_color
        self.hovered = False
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        bg = self.hover_bg if (self.hovered or self.active) else self.bg
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.border_color, self.rect,
                         1, border_radius=self.border_radius)

        if self.active:
            # Garis kiri sebagai indikator aktif
            highlight = pygame.Rect(self.rect.x, self.rect.y + 6, 3, self.rect.height - 12)
            pygame.draw.rect(surface, ACCENT, highlight, border_radius=2)

        if self.font and self.label:
            text_surf = self.font.render(self.label, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def draw_tooltip(self, surface, font_small):
        if self.hovered and self.tooltip:
            tip = font_small.render(self.tooltip, True, TEXT_COLOR)
            tip_rect = tip.get_rect()
            tx = self.rect.right + 8
            ty = self.rect.centery - tip_rect.height // 2
            bg_rect = tip_rect.inflate(12, 6)
            bg_rect.topleft = (tx, ty)
            pygame.draw.rect(surface, PANEL_BG, bg_rect, border_radius=6)
            pygame.draw.rect(surface, ACCENT, bg_rect, 1, border_radius=6)
            surface.blit(tip, (tx + 6, ty + 3))


class ThicknessSlider:
    def __init__(self, x, y, width, min_val=1, max_val=20, initial=2):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])

    def _update_value(self, mx):
        ratio = (mx - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        self.value = int(self.min_val + ratio * (self.max_val - self.min_val))

    def draw(self, surface, font):
        # Track
        pygame.draw.rect(surface, PANEL_BORDER, self.rect, border_radius=10)
        # Fill
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_w = int(ratio * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
        pygame.draw.rect(surface, ACCENT, fill_rect, border_radius=10)
        # Knob
        knob_x = self.rect.x + fill_w
        pygame.draw.circle(surface, WHITE, (knob_x, self.rect.centery), 9)
        pygame.draw.circle(surface, ACCENT, (knob_x, self.rect.centery), 9, 2)
        # Label
        lbl = font.render(f'{self.value}px', True, TEXT_COLOR)
        surface.blit(lbl, (self.rect.right + 8, self.rect.y))


class UI:
    """
    Kelas UI utama yang mengelola seluruh antarmuka.
    """

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Canvas area (di sebelah kanan sidebar)
        self.canvas_rect = pygame.Rect(
            SIDEBAR_WIDTH, TOOLBAR_HEIGHT,
            screen_w - SIDEBAR_WIDTH,
            screen_h - TOOLBAR_HEIGHT
        )

        # Inisialisasi font
        self.font_lg   = pygame.font.SysFont('segoeui', 18, bold=True)
        self.font_md   = pygame.font.SysFont('segoeui', 14)
        self.font_sm   = pygame.font.SysFont('segoeui', 12)
        self.font_icon = pygame.font.SysFont('segoeuiemoji', 20)
        self.font_tool = pygame.font.SysFont('segoeuiemoji', 22)

        # State
        self.active_tool   = 'pencil'
        self.active_color  = (0, 0, 0)
        self.fill_mode     = False
        self.line_style    = 'solid'   # 'solid' atau 'dashed'
        self.animate_on    = False
        self.show_grid     = False

        # Komponen UI
        self.thickness_slider = ThicknessSlider(
            SIDEBAR_WIDTH // 2 - 60, 0, 120, 1, 20, 2
        )
        self._build_tool_buttons()
        self._build_action_buttons()

    @property
    def thickness(self):
        return self.thickness_slider.value

    def _build_tool_buttons(self):
        self.tool_buttons = []
        btn_w, btn_h = SIDEBAR_WIDTH - 24, 33
        start_y = 210
        gap = 4
        for i, tool in enumerate(TOOLS):
            x = 12
            y = start_y + i * (btn_h + gap)
            btn = Button(
                (x, y, btn_w, btn_h),
                label=f"  {tool['label']}  {tool['name']}",
                tooltip=f"{tool['name']} [{tool['shortcut']}]",
                font=self.font_md,
                border_radius=8
            )
            btn.active = (tool['id'] == self.active_tool)
            self.tool_buttons.append((tool['id'], btn))

    def _build_action_buttons(self):
        btn_w = SIDEBAR_WIDTH - 24
        y_base = self.screen_h - 172

        self.btn_animate = Button(
            (12, y_base, btn_w, 30),
            label='▶  Animate',
            font=self.font_md,
            border_radius=8
        )
        self.btn_clear = Button(
            (12, y_base + 36, btn_w, 30),
            label='🗑  Clear All',
            font=self.font_md,
            border_radius=8,
            bg=(60, 20, 20),
            hover_bg=(100, 30, 30)
        )
        self.btn_filled = Button(
            (12, y_base + 72, btn_w, 30),
            label='◼  Filled: Off',
            font=self.font_md,
            border_radius=8
        )
        self.btn_dashed = Button(
            (12, y_base + 108, btn_w, 30),
            label='- - Dashed: Off',
            font=self.font_md,
            border_radius=8
        )

        # Undo / Redo buttons di toolbar atas
        half_w = (self.screen_w - SIDEBAR_WIDTH) // 2 - 8
        undo_x = SIDEBAR_WIDTH + 4
        redo_x = SIDEBAR_WIDTH + half_w + 8
        btn_h  = 32
        btn_y  = (TOOLBAR_HEIGHT - btn_h) // 2

        self.btn_undo = Button(
            (undo_x, btn_y, half_w, btn_h),
            label='⟲  Undo  (Ctrl+Z)',
            tooltip='Undo aksi terakhir',
            font=self.font_md,
            border_radius=7,
            bg=(35, 35, 55),
            hover_bg=(55, 55, 90)
        )
        self.btn_redo = Button(
            (redo_x, btn_y, half_w, btn_h),
            label='⟳  Redo  (Ctrl+Y)',
            tooltip='Ulangi aksi yang di-undo',
            font=self.font_md,
            border_radius=7,
            bg=(35, 35, 55),
            hover_bg=(55, 55, 90)
        )

        # State undo/redo (akan di-update dari main.py)
        self.undo_enabled = False
        self.redo_enabled = False

        # Update label sesuai state
        self._update_action_labels()

    def _update_action_labels(self):
        if self.animate_on:
            self.btn_animate.label = '⏹  Stop Animate'
            self.btn_animate.bg = (30, 80, 30)
            self.btn_animate.hover_bg = (40, 110, 40)
        else:
            self.btn_animate.label = '▶  Animate'
            self.btn_animate.bg = PANEL_BG
            self.btn_animate.hover_bg = SELECTED_BG

        self.btn_filled.label = f"◼  Filled: {'On' if self.fill_mode else 'Off'}"
        self.btn_filled.active = self.fill_mode

        self.btn_dashed.label = f"- -  Dashed: {'On' if self.line_style == 'dashed' else 'Off'}"
        self.btn_dashed.active = self.line_style == 'dashed'

    def update_undo_redo_state(self, can_undo: bool, can_redo: bool):
        """Sinkronisasi state tombol undo/redo dari canvas."""
        self.undo_enabled = can_undo
        self.redo_enabled = can_redo

    def handle_event(self, event):
        """
        Proses event UI. Mengembalikan dict action jika ada interaksi.
        """
        action = {}

        # Slider ketebalan
        self.thickness_slider.handle_event(event)

        # Tool buttons
        for tool_id, btn in self.tool_buttons:
            if btn.handle_event(event):
                self.active_tool = tool_id
                for _, b in self.tool_buttons:
                    b.active = False
                btn.active = True
                action['tool'] = tool_id

        # Action buttons
        if self.btn_animate.handle_event(event):
            self.animate_on = not self.animate_on
            self._update_action_labels()
            action['animate'] = self.animate_on

        if self.btn_clear.handle_event(event):
            action['clear'] = True

        if self.btn_filled.handle_event(event):
            self.fill_mode = not self.fill_mode
            self._update_action_labels()
            action['fill_mode'] = self.fill_mode

        if self.btn_dashed.handle_event(event):
            self.line_style = 'dashed' if self.line_style == 'solid' else 'solid'
            self._update_action_labels()
            action['line_style'] = self.line_style

        # Tombol Undo / Redo
        if self.undo_enabled and self.btn_undo.handle_event(event):
            action['undo'] = True
        if self.redo_enabled and self.btn_redo.handle_event(event):
            action['redo'] = True
        # Tetap proses hover meski disabled
        if not self.undo_enabled:
            if event.type == pygame.MOUSEMOTION:
                self.btn_undo.hovered = self.btn_undo.rect.collidepoint(event.pos)
        if not self.redo_enabled:
            if event.type == pygame.MOUSEMOTION:
                self.btn_redo.hovered = self.btn_redo.rect.collidepoint(event.pos)

        # Klik palet warna
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            color = self._get_palette_click(event.pos)
            if color is not None:
                self.active_color = color
                action['color'] = color

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            shortcuts = {tool['shortcut']: tool['id'] for tool in TOOLS}
            key_char = pygame.key.name(event.key).upper()
            if key_char in shortcuts:
                self.active_tool = shortcuts[key_char]
                for tid, btn in self.tool_buttons:
                    btn.active = (tid == self.active_tool)
                action['tool'] = self.active_tool

        return action

    def _get_palette_click(self, pos):
        """Cek apakah user mengklik satu dari kotak palet warna."""
        start_x = 12
        start_y = PALETTE_START_Y
        for i, color in enumerate(COLOR_PALETTE):
            col = i % PALETTE_COLS
            row = i // PALETTE_COLS
            rx = start_x + col * (SWATCH_SIZE + SWATCH_GAP)
            ry = start_y + row * (SWATCH_SIZE + SWATCH_GAP)
            rect = pygame.Rect(rx, ry, SWATCH_SIZE, SWATCH_SIZE)
            if rect.collidepoint(pos):
                return color
        return None

    def draw(self, surface):
        # ── Sidebar ──
        sidebar_rect = pygame.Rect(0, 0, SIDEBAR_WIDTH, self.screen_h)
        pygame.draw.rect(surface, PANEL_BG, sidebar_rect)
        pygame.draw.line(surface, PANEL_BORDER,
                         (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, self.screen_h), 1)

        # Judul
        title = self.font_lg.render('🎨 MiniPaint', True, ACCENT)
        surface.blit(title, (14, 8))
        subtitle = self.font_sm.render('Grafika Komputer Project', True, TEXT_DIM)
        surface.blit(subtitle, (14, 30))

        # ── Palet Warna (24 warna, 6 kolom) ──
        start_x = 12
        start_y = PALETTE_START_Y
        total_rows = len(COLOR_PALETTE) // PALETTE_COLS
        for i, color in enumerate(COLOR_PALETTE):
            col = i % PALETTE_COLS
            row = i // PALETTE_COLS
            rx = start_x + col * (SWATCH_SIZE + SWATCH_GAP)
            ry = start_y + row * (SWATCH_SIZE + SWATCH_GAP)
            rect = pygame.Rect(rx, ry, SWATCH_SIZE, SWATCH_SIZE)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            if color == self.active_color:
                pygame.draw.rect(surface, WHITE, rect, 2, border_radius=4)

        # Indikator warna aktif (kotak kecil di kanan grid)
        palette_w = PALETTE_COLS * (SWATCH_SIZE + SWATCH_GAP) - SWATCH_GAP
        indicator_x = start_x + palette_w + 4
        indicator_y = start_y
        indicator_h = total_rows * (SWATCH_SIZE + SWATCH_GAP) - SWATCH_GAP
        pygame.draw.rect(surface, self.active_color,
                         (indicator_x, indicator_y, SIDEBAR_WIDTH - indicator_x - 4, indicator_h),
                         border_radius=5)
        pygame.draw.rect(surface, WHITE,
                         (indicator_x, indicator_y, SIDEBAR_WIDTH - indicator_x - 4, indicator_h),
                         1, border_radius=5)
        # Label warna hex di dalam indikator
        r, g, b = self.active_color
        hex_str = f'#{r:02X}{g:02X}{b:02X}'
        hex_surf = self.font_sm.render(hex_str, True, WHITE
                                       if (r + g + b) < 380 else BLACK)
        hex_rect = hex_surf.get_rect(
            center=(indicator_x + (SIDEBAR_WIDTH - indicator_x - 4) // 2,
                    indicator_y + indicator_h // 2)
        )
        surface.blit(hex_surf, hex_rect)

        # Separator
        sep_y = start_y + total_rows * (SWATCH_SIZE + SWATCH_GAP) + 2
        pygame.draw.line(surface, PANEL_BORDER, (8, sep_y), (SIDEBAR_WIDTH - 8, sep_y))

        # Slider ketebalan
        th_label = self.font_sm.render('Thickness / Eraser Size', True, TEXT_DIM)
        surface.blit(th_label, (12, sep_y + 4))
        self.thickness_slider.rect.y = sep_y + 20
        self.thickness_slider.rect.x = 12
        self.thickness_slider.rect.width = SIDEBAR_WIDTH - 60
        self.thickness_slider.draw(surface, self.font_sm)

        # Separator 2
        sep2_y = sep_y + 46
        pygame.draw.line(surface, PANEL_BORDER, (8, sep2_y), (SIDEBAR_WIDTH - 8, sep2_y))

        # Tool buttons
        for _, btn in self.tool_buttons:
            btn.draw(surface)
            btn.draw_tooltip(surface, self.font_sm)

        # Separator sebelum action buttons
        sep3_y = self.screen_h - 178
        pygame.draw.line(surface, PANEL_BORDER, (8, sep3_y), (SIDEBAR_WIDTH - 8, sep3_y))

        # Action buttons
        self.btn_animate.draw(surface)
        self.btn_clear.draw(surface)
        self.btn_filled.draw(surface)
        self.btn_dashed.draw(surface)

        # ── Toolbar Atas ──
        toolbar_rect = pygame.Rect(SIDEBAR_WIDTH, 0, self.screen_w - SIDEBAR_WIDTH, TOOLBAR_HEIGHT)
        pygame.draw.rect(surface, PANEL_BG, toolbar_rect)
        pygame.draw.line(surface, PANEL_BORDER,
                         (SIDEBAR_WIDTH, TOOLBAR_HEIGHT),
                         (self.screen_w, TOOLBAR_HEIGHT), 1)

        # Tombol Undo & Redo di toolbar
        undo_color = TEXT_COLOR if self.undo_enabled else TEXT_DIM
        redo_color = TEXT_COLOR if self.redo_enabled else TEXT_DIM
        self.btn_undo.text_color = undo_color
        self.btn_redo.text_color = redo_color
        self.btn_undo.draw(surface)
        self.btn_redo.draw(surface)

        # Garis disabled di atas tombol jika tidak bisa di-klik
        if not self.undo_enabled:
            overlay = pygame.Surface(
                (self.btn_undo.rect.width, self.btn_undo.rect.height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 80))
            surface.blit(overlay, self.btn_undo.rect.topleft)
        if not self.redo_enabled:
            overlay = pygame.Surface(
                (self.btn_redo.rect.width, self.btn_redo.rect.height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 80))
            surface.blit(overlay, self.btn_redo.rect.topleft)

        # Kotak preview warna di toolbar
        pygame.draw.rect(surface, self.active_color,
                         (self.screen_w - 70, 14, 32, 32), border_radius=6)
        pygame.draw.rect(surface, WHITE,
                         (self.screen_w - 70, 14, 32, 32), 1, border_radius=6)

        # Hint keyboard
        hint = self.font_sm.render(
            '[Ctrl+Z] Undo  [Ctrl+Y] Redo  [Del] hapus  [[ / ]] rotasi  [+/-] scale  [Esc] deselect',
            True, TEXT_DIM
        )
        surface.blit(hint, (SIDEBAR_WIDTH + 16, self.screen_h - 22))

    def is_on_canvas(self, pos):
        return self.canvas_rect.collidepoint(pos)

    def canvas_pos(self, pos):
        """Konversi posisi layar ke posisi relatif kanvas."""
        return (pos[0] - self.canvas_rect.x, pos[1] - self.canvas_rect.y)

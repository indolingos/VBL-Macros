"""VBL Macro — Liquid Glass inspired desktop dashboard.

Macro behavior intentionally matches the existing app:
` -> right click, space, left click
r -> right click, space
Hotkeys only fire while armed and, on Windows, while Roblox is focused.
"""

import ctypes
import math
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

import keyboard
import pydirectinput

pydirectinput.PAUSE = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = sys.platform.startswith("win")
ROBLOX_TITLE_MATCH = "roblox"

# Neutral Liquid Glass-like palette: the environment supplies the color.
BG = "#0c0e13"
GLASS = "#191c23"
GLASS_HI = "#232832"
GLASS_INSET = "#11141a"
EDGE = "#3a404c"
EDGE_SOFT = "#2a2f38"
TEXT = "#f6f7fb"
MUTED = "#a2a7b2"
DIM = "#6f7581"
WHITE = "#ffffff"
BLUE = "#6ea8ff"
CYAN = "#70ddff"
PURPLE = "#b895ff"
GREEN = "#76e6ae"
RED = "#ff7083"
YELLOW = "#ffd76d"
BLACK = "#050608"

running = False
roblox_focused = False
event_count = 0
last_action = "—"
last_action_time = "—"
session_start = time.time()
held = set()


def resource_path(name):
    base = getattr(sys, "_MEIPASS", BASE_DIR) if getattr(sys, "frozen", False) else BASE_DIR
    return os.path.join(base, name)


def family(preferred, fallbacks):
    try:
        available = set(tkfont.families())
    except Exception:
        available = set()
    if preferred in available:
        return preferred
    for item in fallbacks:
        if item in available:
            return item
    return "TkDefaultFont"


def rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, amount):
    ar, ag, ab = rgb(a)
    br, bg, bb = rgb(b)
    amount = max(0.0, min(1.0, amount))
    return "#%02x%02x%02x" % (
        round(ar + (br - ar) * amount),
        round(ag + (bg - ag) * amount),
        round(ab + (bb - ab) * amount),
    )


def rr(x1, y1, x2, y2, radius):
    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    return [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]


def active_title():
    if not IS_WINDOWS:
        return ""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def is_roblox():
    return ROBLOX_TITLE_MATCH in active_title().lower()


def apply_windows_backdrop(root):
    """Ask Windows 11 for an acrylic backdrop when available; silently fall back."""
    if not IS_WINDOWS:
        return
    try:
        hwnd = root.winfo_id()
        dwmapi = ctypes.windll.dwmapi
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        # Windows 11: 3 = Acrylic.
        value = ctypes.c_int(3)
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass


def combo_tilde():
    pydirectinput.rightClick()
    pydirectinput.press("space")
    pydirectinput.leftClick()


def combo_r():
    pydirectinput.rightClick()
    pydirectinput.press("space")


def make_handler(key, action, app):
    def on_event(event):
        global event_count, last_action, last_action_time
        if not running:
            return
        if IS_WINDOWS and not roblox_focused:
            return
        if event.event_type == "down" and key not in held:
            held.add(key)
            action()
            event_count += 1
            last_action = key.upper()
            last_action_time = time.strftime("%H:%M:%S")
            app.root.after(0, app.macro_fired, key)
            app.log(f"{last_action_time}   {key.upper()}   COMBO EXECUTED   #{event_count}")
        elif event.event_type == "up":
            held.discard(key)
    return on_event


class AmbientBackground(tk.Canvas):
    """Animated ambient light pools behind the frosted interface."""
    def __init__(self, master):
        super().__init__(master, bg=BG, highlightthickness=0)
        self.phase = 0.0
        self.bind("<Configure>", self.draw)
        self.after(55, self.tick)

    def draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        pools = [
            (w * 0.16 + math.sin(self.phase) * 18, h * 0.17, 205, PURPLE, 0.92),
            (w * 0.84 + math.cos(self.phase * 0.7) * 22, h * 0.34, 240, CYAN, 0.94),
            (w * 0.62, h * 0.94 + math.sin(self.phase * 0.55) * 16, 300, BLUE, 0.96),
        ]
        for cx, cy, radius, color, fade in pools:
            for ring in range(9, 0, -1):
                r = radius * ring / 9
                self.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    fill=mix(color, BG, fade - ring * 0.018), outline="",
                )
        self.create_rectangle(1, 1, w - 1, h - 1, outline=mix(BG, WHITE, 0.035), width=1)
        self.phase += 0.012

    def tick(self):
        self.draw()
        self.after(55, self.tick)


class SpecularBar(tk.Canvas):
    """A subtle moving reflection rather than a constant RGB strip."""
    def __init__(self, master):
        super().__init__(master, height=3, bg=BG, highlightthickness=0)
        self.phase = 0.0
        self.flash = 0.0
        self.bind("<Configure>", self.draw)
        self.after(32, self.tick)

    def pulse(self):
        self.flash = 1.0

    def draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2:
            return
        self.create_line(34, 1, w - 34, 1, fill=mix(GLASS_HI, WHITE, 0.32), width=1.0)
        sweep = ((math.sin(self.phase) + 1) / 2) * (w + 100) - 50
        glow = mix(WHITE, BLUE, 0.35)
        width = 4 + self.flash * 7
        self.create_line(sweep, 0, sweep + width, h, fill=glow, width=1.5 + self.flash)

    def tick(self):
        self.phase += 0.018
        self.flash *= 0.86
        self.draw()
        self.after(32, self.tick)


class GlassSurface(tk.Frame):
    """Rounded, layered surface with an inner highlight and soft depth."""
    def __init__(self, master, accent=BLUE):
        super().__init__(master, bg=BG)
        self.accent = accent
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=GLASS)
        self.item = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", self.draw)

    def finalize(self, height=None):
        self.body.update_idletasks()
        self.canvas.configure(height=height or self.body.winfo_reqheight())
        self.draw()

    def draw(self, _=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 6 or h < 6:
            return
        self.canvas.delete("surface")
        self.canvas.create_polygon(
            rr(2, 5, w - 2, h + 1, 25),
            fill=mix(BLACK, BG, 0.10), outline="", smooth=True, tags="surface",
        )
        self.canvas.create_polygon(
            rr(1, 1, w - 1, h - 1, 24),
            fill=mix(GLASS, self.accent, 0.025),
            outline=EDGE_SOFT, width=1, smooth=True, tags="surface",
        )
        self.canvas.create_polygon(
            rr(4, 4, w - 4, h - 4, 20),
            fill=GLASS,
            outline=EDGE, width=1, smooth=True, tags="surface",
        )
        self.canvas.create_line(
            27, 5, w - 27, 5,
            fill=mix(WHITE, self.accent, 0.42), width=1.3,
            capstyle="round", tags="surface",
        )
        self.canvas.create_line(
            42, h - 5, w - 42, h - 5,
            fill=mix(GLASS, WHITE, 0.055), width=1,
            capstyle="round", tags="surface",
        )
        self.canvas.tag_lower("surface")
        self.canvas.coords(self.item, 0, 0)
        self.canvas.itemconfigure(self.item, width=w, height=h)


class GlassButton(tk.Canvas):
    def __init__(self, master, text, command, accent):
        super().__init__(master, height=56, bg=GLASS, highlightthickness=0, cursor="hand2")
        self.text = text
        self.command = command
        self.accent = accent
        self.hover = False
        self.pressed = False
        self.bind("<Configure>", self.draw)
        self.bind("<Enter>", lambda _: self.set_hover(True))
        self.bind("<Leave>", lambda _: self.set_hover(False))
        self.bind("<Button-1>", lambda _: self.set_pressed(True))
        self.bind("<ButtonRelease-1>", self.release)

    def set_hover(self, value):
        self.hover = value
        self.draw()

    def set_pressed(self, value):
        self.pressed = value
        self.draw()

    def draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8:
            return
        tint = 0.11 if self.hover else 0.045
        fill = mix(GLASS_HI, self.accent, tint)
        if self.pressed:
            fill = mix(fill, BLACK, 0.14)
        self.create_polygon(rr(1, 1, w - 1, h - 1, h / 2), fill=fill, outline=EDGE_SOFT, width=1, smooth=True)
        self.create_line(24, 4, w - 24, 4, fill=mix(WHITE, self.accent, 0.48), width=1.1, capstyle="round")
        self.create_text(
            w / 2, h / 2,
            text=self.text,
            fill=TEXT,
            font=(family("Segoe UI Variable Semibold", ["Segoe UI Semibold", "Segoe UI"]), 11, "bold"),
        )

    def release(self, event):
        self.pressed = False
        self.draw()
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self.command()

    def set(self, text, accent):
        self.text, self.accent = text, accent
        self.draw()


class StatusPill(tk.Canvas):
    def __init__(self, master, text, accent, width=176):
        super().__init__(master, width=width, height=32, bg=BG, highlightthickness=0)
        self.text, self.accent = text, accent
        self.bind("<Configure>", self.draw)

    def draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_polygon(rr(0, 0, w, h, h / 2), fill=mix(GLASS, self.accent, 0.08), outline=EDGE_SOFT, width=1, smooth=True)
        self.create_line(18, 4, w - 18, 4, fill=mix(WHITE, self.accent, 0.42), width=1, capstyle="round")
        self.create_oval(11, h / 2 - 4, 19, h / 2 + 4, fill=self.accent, outline="")
        self.create_text(27, h / 2, anchor="w", text=self.text, fill=self.accent,
                         font=(family("Segoe UI", ["Arial"]), 8, "bold"))

    def set(self, text, accent):
        self.text, self.accent = text, accent
        self.draw()


class FocusPill(tk.Canvas):
    def __init__(self, master, width=360):
        super().__init__(master, width=width, height=38, bg=BG, highlightthickness=0)
        self.text = "ROBLOX NOT FOCUSED"
        self.accent = RED
        self.bind("<Configure>", self.draw)

    def draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_polygon(rr(0, 0, w, h, h / 2), fill=mix(GLASS, self.accent, 0.07), outline=EDGE_SOFT, width=1, smooth=True)
        self.create_line(22, 4, w - 22, 4, fill=mix(WHITE, self.accent, 0.34), width=1, capstyle="round")
        self.create_oval(13, h / 2 - 4, 21, h / 2 + 4, fill=self.accent, outline="")
        self.create_text(31, h / 2, anchor="w", text=self.text, fill=self.accent,
                         font=(family("Segoe UI", ["Arial"]), 8, "bold"))

    def set(self, text, accent):
        self.text, self.accent = text, accent
        self.draw()


class EnergyCore(tk.Canvas):
    """Soft luminous orb that behaves like a glass control rather than a neon gadget."""
    def __init__(self, master):
        super().__init__(master, width=136, height=136, bg=GLASS, highlightthickness=0)
        self.phase = 0.0
        self.burst = 0.0
        self.state = "idle"
        self.after(38, self.tick)

    def set_state(self, state):
        self.state = state

    def fire(self):
        self.burst = 1.0

    def tick(self):
        self.delete("all")
        accent = {"idle": DIM, "waiting": YELLOW, "live": GREEN}.get(self.state, DIM)
        pulse = (math.sin(self.phase) + 1) / 2
        cx = cy = 68
        glow = pulse * 5 + self.burst * 12
        for radius, strength in ((43 + glow, 0.93), (35 + glow, 0.87), (28 + glow, 0.72)):
            self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                             fill=mix(accent, GLASS, strength), outline="")
        outer = 39 + pulse * 1.8 + self.burst * 5
        self.create_oval(cx - outer, cy - outer, cx + outer, cy + outer,
                         fill=mix(GLASS_HI, accent, 0.03), outline=mix(WHITE, accent, 0.4), width=1)
        inner = 26 + pulse * 1.2 + self.burst * 3
        self.create_oval(cx - inner, cy - inner, cx + inner, cy + inner,
                         fill=mix(GLASS_INSET, accent, 0.13), outline="")
        self.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=WHITE, outline="")
        self.create_oval(cx - 4, cy - 5, cx - 1, cy - 2, fill=accent, outline="")
        self.create_text(cx, 124,
                         text={"idle": "STANDBY", "waiting": "WAITING", "live": "LIVE"}.get(self.state, "STANDBY"),
                         fill=accent,
                         font=(family("Segoe UI Semibold", ["Segoe UI"]), 8, "bold"))
        self.phase += 0.085
        self.burst *= 0.74
        self.after(38, self.tick)


class ComboVisualizer(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, height=78, bg=GLASS, highlightthickness=0)
        self.progress = 0
        self.steps = 3

    def trigger(self, steps=3):
        self.progress = 0
        self.steps = steps
        self.after(60, self.advance)

    def advance(self):
        if self.progress < self.steps:
            self.progress += 1
            self.draw()
            self.after(86, self.advance)
        else:
            self.after(260, self.reset)

    def reset(self):
        self.progress = 0
        self.draw()

    def draw(self, _=None):
        self.delete("all")
        w, _h = self.winfo_width(), self.winfo_height()
        nodes = [(44, "RMB", CYAN), (w / 2, "SPACE", PURPLE), (w - 44, "LMB", BLUE)]
        for i, (x, label, accent) in enumerate(nodes, 1):
            active = i <= self.progress
            fill = mix(GLASS_HI, accent, 0.82 if active else 0.05)
            outline = accent if active else EDGE_SOFT
            self.create_oval(x - 18, 11, x + 18, 47, fill=fill, outline=outline, width=1)
            self.create_text(x, 29, text=str(i), fill=BLACK if active else MUTED,
                             font=(family("Segoe UI Semibold", ["Segoe UI"]), 9, "bold"))
            self.create_text(x, 61, text=label, fill=accent if active else MUTED,
                             font=(family("Cascadia Mono", ["Consolas"]), 7, "bold"))
        for x1, x2 in ((62, w / 2 - 20), (w / 2 + 20, w - 62)):
            self.create_line(x1, 29, x2, 29, fill=EDGE_SOFT, width=2)


class EventToast:
    def __init__(self, root):
        self.label = tk.Label(
            root, text="", bg=GLASS_HI, fg=TEXT,
            font=(family("Segoe UI Semibold", ["Segoe UI"]), 9, "bold"),
            padx=16, pady=8, bd=0,
        )
        self.after_id = None

    def show(self, text, accent):
        self.label.config(text=text, fg=accent)
        self.label.place(relx=1.0, rely=1.0, x=-26, y=-22, anchor="se")
        if self.after_id:
            try:
                self.label.after_cancel(self.after_id)
            except Exception:
                pass
        self.after_id = self.label.after(1200, self.hide)

    def hide(self):
        self.label.place_forget()


class Overlay:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        try:
            self.win.attributes("-alpha", 0.96)
        except Exception:
            pass
        matte = "#010203"
        if IS_WINDOWS:
            try:
                self.win.configure(bg=matte)
                self.win.attributes("-transparentcolor", matte)
            except Exception:
                pass
        else:
            self.win.configure(bg=BG)
        self.W, self.H = 320, 92
        screen_h = self.win.winfo_screenheight()
        self.win.geometry(f"{self.W}x{self.H}+24+{screen_h-self.H-84}")
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H,
                                bg=matte if IS_WINDOWS else BG, highlightthickness=0)
        self.canvas.pack()
        self.state = "stopped"
        self.phase = 0.0
        self.drag = (0, 0)
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.animate()

    def start_drag(self, event):
        self.drag = (event.x, event.y)

    def drag_move(self, _):
        self.win.geometry(f"+{self.win.winfo_pointerx()-self.drag[0]}+{self.win.winfo_pointery()-self.drag[1]}")

    def update(self, armed, focused):
        self.state = "stopped" if not armed else ("waiting" if IS_WINDOWS and not focused else "active")

    def animate(self):
        self.canvas.delete("all")
        accent = {"stopped": RED, "waiting": YELLOW, "active": GREEN}[self.state]
        title = {"stopped": "OFFLINE", "waiting": "WAITING", "active": "LIVE"}[self.state]
        detail = {
            "stopped": "Macro disarmed",
            "waiting": "Waiting for Roblox focus",
            "active": "Hotkeys ready  •  ` + R",
        }[self.state]
        self.canvas.create_polygon(rr(1, 1, self.W - 1, self.H - 1, 24), fill=GLASS, outline=EDGE, width=1, smooth=True)
        self.canvas.create_line(24, 5, self.W - 24, 5,
                                fill=mix(WHITE, accent, 0.42), width=1.2, capstyle="round")
        pulse = (math.sin(self.phase) + 1) / 2
        r = 6 + pulse
        self.canvas.create_oval(26-r-4, 43-r-4, 26+r+4, 43+r+4,
                                fill=mix(accent, GLASS, 0.78), outline="")
        self.canvas.create_oval(26-r, 43-r, 26+r, 43+r, fill=accent, outline="")
        self.canvas.create_oval(24, 41, 26, 43, fill=WHITE, outline="")
        self.canvas.create_text(50, 33, anchor="w", text=title, fill=accent,
                                font=(family("Segoe UI Semibold", ["Segoe UI"]), 13, "bold"))
        self.canvas.create_text(50, 57, anchor="w", text=detail, fill=MUTED,
                                font=(family("Segoe UI", ["Arial"]), 9))
        self.phase += 0.09
        self.win.after(48, self.animate)


class App:
    def __init__(self, root):
        self.root = root
        self.fd = family("Segoe UI Variable Semibold", ["Segoe UI Semibold", "Segoe UI"])
        self.ft = family("Segoe UI Variable", ["Segoe UI"])
        self.fm = family("Cascadia Mono", ["Consolas", "Courier New"])

        root.title("VBL Macro")
        root.configure(bg=BG)
        root.geometry("620x820")
        root.minsize(560, 740)
        try:
            root.attributes("-alpha", 0.975)
        except Exception:
            pass
        apply_windows_backdrop(root)

        ico, png = resource_path("app_icon.ico"), resource_path("icon_512.png")
        try:
            if IS_WINDOWS and os.path.exists(ico):
                root.iconbitmap(default=ico)
            elif os.path.exists(png):
                self.icon = tk.PhotoImage(file=png)
                root.iconphoto(True, self.icon)
        except Exception:
            pass

        self.bg = AmbientBackground(root)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.specular = SpecularBar(root)
        self.specular.place(x=0, y=0, relwidth=1, height=3)

        shell = tk.Frame(root, bg=BG)
        shell.place(x=26, y=26, relwidth=0.916, relheight=0.93)

        top = tk.Frame(shell, bg=BG)
        top.pack(fill="x", pady=(0, 18))
        brand = tk.Frame(top, bg=BG)
        brand.pack(side="left")
        tk.Label(brand, text="VBL", font=(self.fd, 10, "bold"), fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(brand, text="Macro", font=(self.fd, 25, "bold"), fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(brand, text="LIQUID GLASS INPUT LAYER  •  ROBLOX", font=(self.ft, 8), fg=MUTED, bg=BG).pack(anchor="w")
        self.status = StatusPill(top, "OFFLINE", RED, 162)
        self.status.pack(side="right", pady=8)

        focus_row = tk.Frame(shell, bg=BG)
        focus_row.pack(fill="x", pady=(0, 14))
        self.focus = FocusPill(focus_row)
        self.focus.pack(side="left", fill="x", expand=True)
        self.count = tk.Label(focus_row, text="0 FIRES", font=(self.fm, 8, "bold"), fg=TEXT, bg=BG)
        self.count.pack(side="right", padx=(12, 0))

        master = GlassSurface(shell, BLUE)
        master.pack(fill="x", pady=(0, 14))
        mb = master.body
        cap = tk.Frame(mb, bg=GLASS)
        cap.pack(fill="x", padx=20, pady=(16, 5))
        tk.Label(cap, text="MASTER CONTROL", font=(self.ft, 9, "bold"), fg=MUTED, bg=GLASS).pack(side="left")
        self.session = tk.Label(cap, text="SESSION 00:00:00", font=(self.fm, 8), fg=DIM, bg=GLASS)
        self.session.pack(side="right")

        center = tk.Frame(mb, bg=GLASS)
        center.pack(fill="x", padx=18, pady=(2, 7))
        self.core = EnergyCore(center)
        self.core.pack(side="left", padx=(0, 16))
        detail = tk.Frame(center, bg=GLASS)
        detail.pack(side="left", fill="both", expand=True, pady=(13, 0))
        tk.Label(detail, text="ENGINE STATUS", font=(self.ft, 8, "bold"), fg=MUTED, bg=GLASS).pack(anchor="w")
        self.engine_status = tk.Label(detail, text="STANDBY", font=(self.fd, 20, "bold"), fg=TEXT, bg=GLASS)
        self.engine_status.pack(anchor="w", pady=(4, 2))
        self.last = tk.Label(detail, text="Last action  •  —", font=(self.fm, 8), fg=DIM, bg=GLASS)
        self.last.pack(anchor="w")
        tk.Label(detail, text="Hotkeys:  `  +  R", font=(self.fm, 8), fg=MUTED, bg=GLASS).pack(anchor="w", pady=(11, 0))

        self.toggle = GlassButton(mb, "START MACRO", self.toggle_macro, BLUE)
        self.toggle.pack(fill="x", padx=20, pady=(0, 10))
        foot = tk.Frame(mb, bg=GLASS)
        foot.pack(fill="x", padx=22, pady=(0, 16))
        self.engine_hint = tk.Label(foot, text="Focus protection ON", font=(self.ft, 8), fg=DIM, bg=GLASS)
        self.engine_hint.pack(side="left")
        tk.Label(foot, text="ESC  QUIT", font=(self.fm, 8), fg=DIM, bg=GLASS).pack(side="right")
        master.finalize()

        combos = GlassSurface(shell, PURPLE)
        combos.pack(fill="x", pady=(0, 14))
        cb = combos.body
        head = tk.Frame(cb, bg=GLASS)
        head.pack(fill="x", padx=20, pady=(14, 5))
        tk.Label(head, text="COMBO PROFILES", font=(self.ft, 9, "bold"), fg=MUTED, bg=GLASS).pack(side="left")
        tk.Label(head, text="2 PROFILES", font=(self.fm, 8, "bold"), fg=MUTED, bg=GLASS).pack(side="right")
        self.combo_row(cb, "`", "RIGHT CLICK  →  SPACE  →  LEFT CLICK", CYAN, "3-STEP")
        self.combo_row(cb, "R", "RIGHT CLICK  →  SPACE", PURPLE, "2-STEP")
        self.visual = ComboVisualizer(cb)
        self.visual.pack(fill="x", padx=20, pady=(8, 2))
        tk.Label(cb, text="Live stages illuminate as each input fires.", font=(self.ft, 8), fg=DIM, bg=GLASS).pack(anchor="w", padx=20, pady=(0, 13))
        combos.finalize()

        telemetry = GlassSurface(shell, CYAN)
        telemetry.pack(fill="both", expand=True, pady=(0, 10))
        tb = telemetry.body
        th = tk.Frame(tb, bg=GLASS)
        th.pack(fill="x", padx=20, pady=(14, 8))
        tk.Label(th, text="SESSION TELEMETRY", font=(self.ft, 9, "bold"), fg=MUTED, bg=GLASS).pack(side="left")
        self.live = tk.Label(th, text="● IDLE", font=(self.ft, 8, "bold"), fg=DIM, bg=GLASS)
        self.live.pack(side="right")

        stats = tk.Frame(tb, bg=GLASS)
        stats.pack(fill="x", padx=20, pady=(0, 9))
        self.stat_labels = []
        for title, value, accent in (
            ("TOTAL FIRES", "0", CYAN),
            ("LAST KEY", "—", PURPLE),
            ("LAST TIME", "—", BLUE),
            ("UPTIME", "00:00:00", GREEN),
        ):
            box = tk.Frame(stats, bg=GLASS_INSET)
            box.pack(side="left", fill="both", expand=True, padx=3)
            tk.Frame(box, bg=mix(accent, WHITE, 0.10), height=2).pack(fill="x")
            tk.Label(box, text=title, font=(self.ft, 7, "bold"), fg=MUTED, bg=GLASS_INSET).pack(anchor="w", padx=9, pady=(7, 2))
            lbl = tk.Label(box, text=value, font=(self.fd, 13, "bold"), fg=TEXT, bg=GLASS_INSET)
            lbl.pack(anchor="w", padx=9, pady=(0, 8))
            self.stat_labels.append(lbl)

        tk.Label(tb, text="ACTIVITY", font=(self.ft, 8, "bold"), fg=MUTED, bg=GLASS).pack(anchor="w", padx=20, pady=(2, 5))
        self.box = tk.Text(tb, bg=BLACK, fg="#dbe1ec", insertbackground=TEXT, relief="flat", bd=0,
                           font=(self.fm, 8), height=6, wrap="word", state="disabled", padx=12, pady=10)
        self.box.pack(fill="both", expand=True, padx=17, pady=(0, 15))
        telemetry.canvas.configure(height=222)

        self.toast = EventToast(root)
        self.overlay = Overlay(root)

        keyboard.hook_key("`", make_handler("`", combo_tilde, self))
        keyboard.hook_key("r", make_handler("r", combo_r, self))
        keyboard.add_hotkey("esc", self.request_exit, suppress=False)

        self.last_focus = None
        if IS_WINDOWS:
            threading.Thread(target=self.poll_roblox, daemon=True).start()
        threading.Thread(target=self.poll_overlay, daemon=True).start()
        root.after(250, self.update_session)

        self.log("System initialized — Liquid Glass layer ready.")
        if IS_WINDOWS:
            self.log("Roblox focus protection enabled.")
        self.log("Press START MACRO to arm input.")

    def combo_row(self, parent, key, text, accent, tag):
        row = tk.Frame(parent, bg=GLASS)
        row.pack(fill="x", padx=20, pady=4)
        badge = tk.Label(row, text=f" {key} ", font=(self.fm, 10, "bold"), fg=BLACK, bg=accent, padx=8, pady=5)
        badge.pack(side="left")
        tk.Label(row, text=text, font=(self.ft, 10), fg=TEXT, bg=GLASS).pack(side="left", padx=12)
        tk.Label(row, text=tag, font=(self.fm, 7, "bold"), fg=accent, bg=mix(GLASS, accent, 0.08), padx=7, pady=3).pack(side="right")

    def poll_roblox(self):
        global roblox_focused
        while True:
            focused = is_roblox()
            if focused != roblox_focused:
                roblox_focused = focused
                self.root.after(0, self.update_focus, focused)
            time.sleep(0.20)

    def poll_overlay(self):
        previous = None
        while True:
            state = (running, roblox_focused)
            if state != previous:
                previous = state
                self.root.after(0, self.overlay.update, *state)
                self.root.after(0, self.refresh_state)
            time.sleep(0.10)

    def refresh_state(self):
        if running:
            if IS_WINDOWS and not roblox_focused:
                self.live.config(text="● WAITING", fg=YELLOW)
                self.engine_status.config(text="WAITING FOR ROBLOX", fg=YELLOW)
                self.core.set_state("waiting")
                self.engine_hint.config(text="Armed  •  waiting for Roblox focus")
            else:
                self.live.config(text="● LIVE", fg=GREEN)
                self.engine_status.config(text="INPUT LIVE", fg=GREEN)
                self.core.set_state("live")
                self.engine_hint.config(text="Input armed  •  focus lock active")
        else:
            self.live.config(text="● IDLE", fg=DIM)
            self.engine_status.config(text="STANDBY", fg=TEXT)
            self.core.set_state("idle")
            self.engine_hint.config(text="Focus protection ON")
        self.count.config(text=f"{event_count} FIRES")
        self.stat_labels[0].config(text=str(event_count))
        self.stat_labels[1].config(text=last_action)
        self.stat_labels[2].config(text=last_action_time)
        self.stat_labels[3].config(text=self.uptime())
        self.last.config(text=f"Last action  •  {last_action_time if last_action_time != '—' else '—'}")

    def update_focus(self, focused):
        self.focus.set("ROBLOX FOCUSED  •  INPUT READY" if focused else "ROBLOX NOT FOCUSED", GREEN if focused else RED)
        self.refresh_state()

    def toggle_macro(self):
        global running, session_start
        running = not running
        if running:
            session_start = time.time()
            self.toggle.set("STOP MACRO", RED)
            self.status.set("ONLINE", GREEN)
            self.log(f"{time.strftime('%H:%M:%S')}   ENGINE ARMED")
        else:
            self.toggle.set("START MACRO", BLUE)
            self.status.set("OFFLINE", RED)
            self.log(f"{time.strftime('%H:%M:%S')}   ENGINE DISARMED")
        self.refresh_state()
        self.overlay.update(running, roblox_focused)

    def macro_fired(self, key):
        self.core.fire()
        self.visual.trigger(3 if key == "`" else 2)
        if key == "r":
            self.root.after(120, self.visual.draw)
        self.toast.show(f"{key.upper()}  •  COMBO EXECUTED", CYAN if key == "`" else PURPLE)
        self.specular.pulse()

    def uptime(self):
        elapsed = max(0, int(time.time() - session_start)) if running else 0
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_session(self):
        self.refresh_state()
        self.root.after(250, self.update_session)

    def log(self, message):
        def append():
            self.box.configure(state="normal")
            self.box.insert("end", message + "\n")
            lines = int(self.box.index("end-1c").split(".")[0])
            if lines > 80:
                self.box.delete("1.0", "4.0")
            self.box.see("end")
            self.box.configure(state="disabled")
        self.root.after(0, append)

    def request_exit(self):
        self.root.after(0, self.exit_app)

    def exit_app(self):
        try:
            self.overlay.win.destroy()
            self.root.destroy()
        finally:
            os._exit(0)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

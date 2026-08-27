"""VBL Macro — native Qt/QML Liquid Glass desktop shell."""

import ctypes
import os
import sys
import threading
import time

import keyboard
import pydirectinput
from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import Qt

pydirectinput.PAUSE = 0

IS_WINDOWS = sys.platform.startswith("win")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROBLOX_TITLE_MATCH = "roblox"

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


def combo_tilde():
    pydirectinput.rightClick()
    pydirectinput.press("space")
    pydirectinput.leftClick()


def combo_r():
    pydirectinput.rightClick()
    pydirectinput.press("space")


def apply_windows_glass(hwnd):
    """Use the Windows compositor for real desktop blur on supported Windows builds."""
    if not IS_WINDOWS:
        return
    try:
        user32 = ctypes.windll.user32
        dwmapi = ctypes.windll.dwmapi

        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_int),
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.POINTER(ACCENT_POLICY)),
                ("SizeOfData", ctypes.c_size_t),
            ]

        ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
        WCA_ACCENT_POLICY = 19
        # AARRGGBB. Low alpha lets the QML material show while Windows supplies the blur.
        policy = ACCENT_POLICY(ACCENT_ENABLE_ACRYLICBLURBEHIND, 2, 0xB812151C, 0)
        data = WINDOWCOMPOSITIONATTRIBDATA(
            WCA_ACCENT_POLICY, ctypes.pointer(policy), ctypes.sizeof(policy)
        )
        set_attr = user32.SetWindowCompositionAttribute
        set_attr.argtypes = [ctypes.c_void_p, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
        set_attr.restype = ctypes.c_int
        set_attr(ctypes.c_void_p(int(hwnd)), ctypes.byref(data))

        # Prefer rounded corners when Windows exposes the DWM attribute.
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMSBT_MAINWINDOW = 2
        corner = ctypes.c_int(2)
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(int(hwnd)),
            ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
            ctypes.byref(corner),
            ctypes.sizeof(corner),
        )
        _ = DWMSBT_MAINWINDOW
    except Exception:
        pass


class Bridge(QObject):
    runningChanged = Signal()
    focusChanged = Signal()
    eventChanged = Signal()
    statsChanged = Signal()
    toast = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._last_focus = None

    @Property(bool, notify=runningChanged)
    def running(self):
        return running

    @Property(bool, notify=focusChanged)
    def robloxFocused(self):
        return roblox_focused

    @Property(int, notify=statsChanged)
    def eventCount(self):
        return event_count

    @Property(str, notify=statsChanged)
    def lastKey(self):
        return last_action

    @Property(str, notify=statsChanged)
    def lastTime(self):
        return last_action_time

    @Property(str, notify=statsChanged)
    def uptime(self):
        elapsed = max(0, int(time.time() - session_start)) if running else 0
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @Slot()
    def toggle(self):
        global running, session_start
        running = not running
        session_start = time.time() if running else session_start
        self.runningChanged.emit()
        self.statsChanged.emit()
        self.toast.emit("MACRO ARMED" if running else "MACRO DISARMED", "#7BE7B0" if running else "#FF7186")

    @Slot()
    def quit(self):
        global running
        running = False
        QGuiApplication.quit()

    @Slot()
    def minimize(self):
        root = QGuiApplication.instance().activeWindow()
        if root:
            root.showMinimized()

    @Slot()
    def maximize(self):
        root = QGuiApplication.instance().activeWindow()
        if root:
            root.showNormal() if root.isMaximized() else root.showMaximized()

    def fire(self, key):
        self.toast.emit(
            f"{key.upper()}  •  COMBO EXECUTED",
            "#82DFFF" if key == "`" else "#BCA1FF",
        )
        self.eventChanged.emit()
        self.statsChanged.emit()


def make_handler(key, action, bridge):
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
            bridge.fire(key)
        elif event.event_type == "up":
            held.discard(key)
    return on_event


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("VBL Macro")
    app.setOrganizationName("VBL")
    app.setQuitOnLastWindowClosed(True)

    engine = QQmlApplicationEngine()
    bridge = Bridge()
    engine.rootContext().setContextProperty("backend", bridge)
    qml_path = resource_path("LiquidGlass.qml")
    engine.load(QUrl.fromLocalFile(qml_path))
    if not engine.rootObjects():
        raise RuntimeError("Unable to load LiquidGlass.qml")

    root = engine.rootObjects()[0]
    if IS_WINDOWS:
        QTimer.singleShot(50, lambda: apply_windows_glass(int(root.winId())))

    keyboard.hook_key("`", make_handler("`", combo_tilde, bridge))
    keyboard.hook_key("r", make_handler("r", combo_r, bridge))

    def poll():
        global roblox_focused
        if IS_WINDOWS:
            focused = is_roblox()
            if focused != roblox_focused:
                roblox_focused = focused
                bridge.focusChanged.emit()
        bridge.statsChanged.emit()

    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(180)

    result = app.exec()
    keyboard.unhook_all()
    return result


if __name__ == "__main__":
    raise SystemExit(main())

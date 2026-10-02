
import sys
import os
import json
import math
import subprocess
import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QPoint, QRectF, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu

# ============================================================
# Radial Launcher - Windows + PySide6
# Hotkey: WIN + '
# ============================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
HOTKEY_ID = 0x524C  # "RL"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


DEFAULT_CONFIG = {
    "items": [
        {"name": "Discord", "path": "C:\\Program Files\\Discord\\Discord.exe"},
        {"name": "Steam", "path": "C:\\Program Files (x86)\\Steam\\steam.exe"},
        {"name": "Vivaldi", "path": "C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe"},
        {"name": "Explorer", "path": "explorer.exe"},
        {"name": "Notepad", "path": "notepad.exe"},
        {"name": "Calculator", "path": "calc.exe"},
        {"name": "Terminal", "path": "wt.exe"},
        {"name": "ShareX", "path": "C:\\Program Files\\ShareX\\ShareX.exe"}
    ],
    "theme": {
        "background_alpha": 225,
        "circle_alpha": 215,
        "selected_alpha": 245,
        "accent": [80, 170, 255]
    }
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        items = cfg.get("items", [])
        while len(items) < 8:
            items.append({"name": f"Slot {len(items)+1}", "path": ""})
        cfg["items"] = items[:8]
        return cfg
    except Exception:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def launch(path):
    path = os.path.expandvars(os.path.expanduser(path.strip()))
    if not path:
        return

    try:
        # ShellExecute handles .lnk, URLs, folders and executables.
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "open", path, None, None, 1
        )
        if result <= 32:
            # Fallback for commands such as wt.exe/calc.exe.
            subprocess.Popen(path, shell=True)
    except Exception:
        subprocess.Popen(path, shell=True)


class HotkeyWindow(QWidget):
    hotkeyPressed = Signal()

    def nativeEvent(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.hotkeyPressed.emit()
                return True, 0
        return super().nativeEvent(eventType, message)

    def register_hotkey(self):
        # VK_OEM_7 = apostrophe / quotation mark on standard US layout.
        # On Brazilian layouts this physical key is still commonly VK_OEM_7,
        # but the fallback in register_hotkey_physical() covers scan code.
        ok = user32.RegisterHotKey(int(self.winId()), HOTKEY_ID, MOD_WIN, 0xDE)
        return bool(ok)

    def unregister_hotkey(self):
        user32.UnregisterHotKey(int(self.winId()), HOTKEY_ID)


class RadialLauncher(QWidget):
    closed = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.items = config["items"]
        self.selected = -1
        self.mouse_pos = QPoint()
        self.radius = 210
        self.inner_radius = 92

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self.hide()

    def show_centered(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return

        geo = screen.availableGeometry()
        size = 620
        self.setGeometry(
            geo.x() + (geo.width() - size) // 2,
            geo.y() + (geo.height() - size) // 2,
            size,
            size
        )
        self.selected = -1
        self.mouse_pos = self.rect().center()
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.update()

    def closeEvent(self, event):
        self.hide()
        self.closed.emit()
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            return

        # Number shortcuts while wheel is open.
        if Qt.Key_1 <= event.key() <= Qt.Key_8:
            idx = event.key() - Qt.Key_1
            if idx < len(self.items):
                self.selected = idx
                self.execute_selected()
            return

        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.execute_selected()
        elif event.button() == Qt.RightButton:
            self.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.execute_selected()

    def wheel_event(self, delta):
        pass

    def execute_selected(self):
        if 0 <= self.selected < len(self.items):
            item = self.items[self.selected]
            path = item.get("path", "")
            if path:
                self.hide()
                launch(path)

    def calculate_selection(self):
        center = self.rect().center()
        dx = self.mouse_pos.x() - center.x()
        dy = self.mouse_pos.y() - center.y()
        distance = math.hypot(dx, dy)

        if distance < self.inner_radius * 0.7:
            return -1

        # 0 starts at top, then clockwise.
        angle = math.degrees(math.atan2(dy, dx))
        angle = (angle + 90) % 360
        idx = int((angle + 22.5) // 45) % 8

        return idx if idx < len(self.items) else -1

    def paintEvent(self, event):
        self.selected = self.calculate_selection()

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        center = QPoint(self.width() // 2, self.height() // 2)

        # Soft outer glow.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(
            center,
            self.radius + 18,
            self.radius + 18
        )

        # Segment wedges.
        for i in range(8):
            rect = QRectF(
                center.x() - self.radius,
                center.y() - self.radius,
                self.radius * 2,
                self.radius * 2
            )

            selected = i == self.selected
            if selected:
                color = QColor(70, 150, 245, 235)
            else:
                color = QColor(24, 27, 34, 225)

            p.setBrush(QBrush(color))
            p.setPen(QPen(QColor(105, 115, 130, 180), 2))

            # Qt angles: 0° is east, positive is counter-clockwise.
            start = 90 * 16 - i * 45 * 16 - 22.5 * 16
            span = -45 * 16
            p.drawPie(rect, int(start), int(span))

        # Inner disc.
        p.setBrush(QColor(12, 14, 18, 245))
        p.setPen(QPen(QColor(100, 110, 125, 220), 2))
        p.drawEllipse(center, self.inner_radius, self.inner_radius)

        # Center text.
        p.setPen(QColor(230, 235, 242))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        if self.selected >= 0:
            name = self.items[self.selected].get("name", f"Slot {self.selected+1}")
            p.drawText(
                QRectF(center.x()-75, center.y()-28, 150, 56),
                Qt.AlignCenter | Qt.TextWordWrap,
                name
            )
        else:
            p.drawText(
                QRectF(center.x()-80, center.y()-28, 160, 56),
                Qt.AlignCenter | Qt.TextWordWrap,
                "Selecione um aplicativo"
            )

        # Draw labels.
        for i, item in enumerate(self.items):
            angle = math.radians(-90 + i * 45)
            dist = self.radius * 0.69
            x = center.x() + math.cos(angle) * dist
            y = center.y() + math.sin(angle) * dist

            name = item.get("name", f"Slot {i+1}")
            if len(name) > 13:
                name = name[:12] + "…"

            p.setPen(QColor(245, 247, 250))
            p.setFont(QFont("Segoe UI", 9, QFont.Bold if i == self.selected else QFont.Normal))
            p.drawText(
                QRectF(x - 62, y - 18, 124, 36),
                Qt.AlignCenter | Qt.TextWordWrap,
                name
            )

            # Number.
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(180, 190, 205))
            p.drawText(
                QRectF(x - 55, y + 18, 110, 20),
                Qt.AlignCenter,
                str(i + 1)
            )


class AppController(QObject):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.launcher = RadialLauncher(self.config)

        # Hidden window receives WM_HOTKEY.
        self.hotkey_window = HotkeyWindow()
        self.hotkey_window.setWindowFlags(Qt.Tool)
        self.hotkey_window.resize(1, 1)
        self.hotkey_window.move(-100, -100)
        self.hotkey_window.show()
        self.hotkey_window.hide()

        if not self.hotkey_window.register_hotkey():
            print("AVISO: não foi possível registrar Win + '.")
            print("Tente executar o programa como administrador se outro")
            print("software estiver usando a combinação.")

        self.hotkey_window.hotkeyPressed.connect(self.toggle)

        self.tray = QSystemTrayIcon(QIcon(self.make_tray_icon()), QApplication.instance())
        menu = QMenu()
        open_action = menu.addAction("Abrir roda")
        open_action.triggered.connect(self.show_launcher)
        edit_action = menu.addAction("Abrir config.json")
        edit_action.triggered.connect(self.open_config)
        menu.addSeparator()
        quit_action = menu.addAction("Sair")
        quit_action.triggered.connect(self.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Radial Launcher - Win + '")
        self.tray.show()

    def make_tray_icon(self):
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(70, 150, 245))
        p.setPen(Qt.NoPen)
        p.drawEllipse(5, 5, 54, 54)
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Segoe UI", 28, QFont.Bold))
        p.drawText(QRectF(0, 0, 64, 64), Qt.AlignCenter, "R")
        p.end()
        return pix

    def toggle(self):
        if self.launcher.isVisible():
            self.launcher.hide()
        else:
            # Reload config so edits are applied without restarting.
            self.config = load_config()
            self.launcher.config = self.config
            self.launcher.items = self.config["items"]
            self.launcher.show_centered()

    def show_launcher(self):
        self.config = load_config()
        self.launcher.items = self.config["items"]
        self.launcher.show_centered()

    def open_config(self):
        if not os.path.exists(CONFIG_FILE):
            save_config(DEFAULT_CONFIG)
        os.startfile(CONFIG_FILE)

    def quit(self):
        self.hotkey_window.unregister_hotkey()
        self.tray.hide()
        QApplication.quit()


def main():
    if sys.platform != "win32":
        print("Este programa foi feito para Windows.")
        return

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = AppController()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

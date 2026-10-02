
import sys
import os
import json
import math
import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QPoint, QRectF, Signal, QObject, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu, QDialog, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit, QMessageBox, QFileDialog, QGroupBox, QCheckBox
)

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
ICON_FILE = os.path.join(RESOURCE_DIR, "radial.ico")

WM_HOTKEY = 0x0312
HOTKEY_ID = 0x524C
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

user32 = ctypes.windll.user32


DEFAULT_CONFIG = {
    "hotkey": {"modifiers": ["win"], "key": "apostrophe"},
    "items": [
        {"name": "Discord", "path": "C:\\Program Files\\Discord\\Discord.exe"},
        {"name": "Steam", "path": "C:\\Program Files (x86)\\Steam\\steam.exe"},
        {"name": "Vivaldi", "path": "C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe"},
        {"name": "Explorer", "path": "explorer.exe"},
        {"name": "Notepad", "path": "notepad.exe"},
        {"name": "Calculator", "path": "calc.exe"},
        {"name": "Terminal", "path": "wt.exe"},
        {"name": "ShareX", "path": "C:\\Program Files\\ShareX\\ShareX.exe"}
    ]
}

KEYS = {
    "apostrophe": 0xDE,
    "comma": 0xBC, "period": 0xBE, "slash": 0xBF,
    "semicolon": 0xBA, "lbracket": 0xDB, "rbracket": 0xDD,
    "backslash": 0xDC, "minus": 0xBD, "equals": 0xBB,
    "space": 0x20, "tab": 0x09, "enter": 0x0D,
    "esc": 0x1B,
}
for i in range(10):
    KEYS[str(i)] = 0x30 + i
for i in range(26):
    KEYS[chr(97+i)] = 0x41 + i
for i in range(1, 13):
    KEYS[f"f{i}"] = 0x6F + i


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg.setdefault("hotkey", DEFAULT_CONFIG["hotkey"])
        items = cfg.setdefault("items", [])
        while len(items) < 8:
            items.append({"name": f"Slot {len(items)+1}", "path": ""})
        cfg["items"] = items[:8]
        return cfg
    except Exception:
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def launch(path):
    path = os.path.expandvars(os.path.expanduser(path.strip()))
    if not path:
        return
    try:
        result = user32.ShellExecuteW(None, "open", path, None, None, 1)
        if result <= 32:
            os.startfile(path)
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Não foi possível abrir:\n{path}\n\n{e}")


def icon_from_path(path):
    if path and os.path.exists(path):
        icon = QIcon(path)
        if not icon.isNull():
            return icon
        try:
            info = ctypes.windll.shell32.ExtractIconW(None, path, 0)
            if info:
                return QIcon(QPixmap.fromImage(QPixmap()))
        except Exception:
            pass
    return QIcon()


class HotkeyWindow(QWidget):
    hotkeyPressed = Signal()

    def nativeEvent(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.hotkeyPressed.emit()
                return True, 0
        return super().nativeEvent(eventType, message)


class SettingsDialog(QDialog):
    changed = Signal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.cfg = load_config()
        self.setWindowTitle("Radial Launcher - Configurações")
        self.resize(720, 560)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Configuração da roda de atalhos")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        root.addWidget(title)

        root.addWidget(QLabel("Arraste um executável, atalho .lnk, pasta ou arquivo para um slot. O nome será preenchido automaticamente."))

        self.list = QListWidget()
        self.list.setAcceptDrops(True)
        self.list.setDragDropMode(QListWidget.DropOnly)
        self.list.setStyleSheet("QListWidget { font-size: 14px; }")
        self.list.dragEnterEvent = self.list_drag_enter
        self.list.dropEvent = self.list_drop
        root.addWidget(self.list, 1)

        row = QHBoxLayout()
        self.add_btn = QPushButton("Adicionar arquivo...")
        self.add_btn.clicked.connect(self.add_file)
        self.remove_btn = QPushButton("Limpar slot")
        self.remove_btn.clicked.connect(self.clear_slot)
        self.edit_btn = QPushButton("Editar nome")
        self.edit_btn.clicked.connect(self.edit_name)
        row.addWidget(self.add_btn)
        row.addWidget(self.remove_btn)
        row.addWidget(self.edit_btn)
        root.addLayout(row)

        hot_group = QGroupBox("Atalho para abrir a roda")
        hot_layout = QHBoxLayout(hot_group)

        self.mod_win = QCheckBox("Win")
        self.mod_ctrl = QCheckBox("Ctrl")
        self.mod_alt = QCheckBox("Alt")
        self.mod_shift = QCheckBox("Shift")
        self.key_combo = QComboBox()

        for key in ["apostrophe", "space", "tab", "enter", "esc", "a", "b", "c", "d", "e", "f", "g",
                    "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
                    "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]:
            self.key_combo.addItem(key.replace("apostrophe", "'").upper(), key)

        hot_layout.addWidget(self.mod_win)
        hot_layout.addWidget(self.mod_ctrl)
        hot_layout.addWidget(self.mod_alt)
        hot_layout.addWidget(self.mod_shift)
        hot_layout.addWidget(self.key_combo)
        hot_layout.addStretch()
        root.addWidget(hot_group)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.save_btn = QPushButton("Salvar e aplicar")
        self.save_btn.clicked.connect(self.save)
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        bottom.addWidget(self.save_btn)
        bottom.addWidget(self.close_btn)
        root.addLayout(bottom)

    def refresh(self):
        self.list.clear()
        for i, item in enumerate(self.cfg["items"]):
            text = f"{i+1}. {item.get('name', '') or '(vazio)'}"
            if item.get("path"):
                text += f"    —    {item['path']}"
            li = QListWidgetItem(text)
            if item.get("path"):
                li.setIcon(icon_from_path(item["path"]))
            self.list.addItem(li)

        mods = self.cfg.get("hotkey", {}).get("modifiers", ["win"])
        self.mod_win.setChecked("win" in mods)
        self.mod_ctrl.setChecked("ctrl" in mods)
        self.mod_alt.setChecked("alt" in mods)
        self.mod_shift.setChecked("shift" in mods)

        key = self.cfg.get("hotkey", {}).get("key", "apostrophe")
        idx = self.key_combo.findData(key)
        if idx >= 0:
            self.key_combo.setCurrentIndex(idx)

    def list_drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def list_drop(self, event):
        if not event.mimeData().hasUrls():
            return
        urls = event.mimeData().urls()
        if not urls:
            return
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not files:
            return

        row = self.list.indexAt(event.position().toPoint()).row()
        if row < 0:
            row = self.list.currentRow()
        if row < 0:
            row = next((i for i,x in enumerate(self.cfg["items"]) if not x.get("path")), 0)

        path = files[0]
        name = os.path.splitext(os.path.basename(path))[0] or os.path.basename(path)
        if path.lower().endswith(".lnk"):
            name = os.path.splitext(os.path.basename(path))[0]

        self.cfg["items"][row] = {"name": name, "path": path}
        self.refresh()
        self.list.setCurrentRow(row)
        event.acceptProposedAction()

    def add_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Escolha um aplicativo ou atalho", "",
            "Aplicativos e atalhos (*.exe *.lnk *.bat *.cmd);;Todos os arquivos (*.*)"
        )
        if not path:
            return
        row = self.list.currentRow()
        if row < 0:
            row = next((i for i,x in enumerate(self.cfg["items"]) if not x.get("path")), 0)
        name = os.path.splitext(os.path.basename(path))[0]
        self.cfg["items"][row] = {"name": name, "path": path}
        self.refresh()
        self.list.setCurrentRow(row)

    def clear_slot(self):
        row = self.list.currentRow()
        if row >= 0:
            self.cfg["items"][row] = {"name": f"Slot {row+1}", "path": ""}
            self.refresh()
            self.list.setCurrentRow(row)

    def edit_name(self):
        row = self.list.currentRow()
        if row < 0:
            return
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Nome do atalho", "Nome:", text=self.cfg["items"][row].get("name", ""))
        if ok and name.strip():
            self.cfg["items"][row]["name"] = name.strip()
            self.refresh()
            self.list.setCurrentRow(row)

    def save(self):
        mods = []
        if self.mod_win.isChecked(): mods.append("win")
        if self.mod_ctrl.isChecked(): mods.append("ctrl")
        if self.mod_alt.isChecked(): mods.append("alt")
        if self.mod_shift.isChecked(): mods.append("shift")

        if not mods:
            QMessageBox.warning(self, "Atalho inválido", "Selecione pelo menos um modificador.")
            return

        self.cfg["hotkey"] = {
            "modifiers": mods,
            "key": self.key_combo.currentData()
        }
        save_config(self.cfg)

        if not self.controller.apply_hotkey():
            QMessageBox.warning(
                self, "Atalho não disponível",
                "O Windows não conseguiu registrar essa combinação.\n"
                "Ela pode já estar sendo usada por outro programa."
            )
            return

        self.controller.reload_config()
        self.changed.emit()
        QMessageBox.information(self, "Salvo", "Configuração salva e aplicada.")
        self.refresh()


class RadialLauncher(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.items = controller.config["items"]
        self.selected = -1
        self.mouse_pos = QPoint()
        self.radius = 220
        self.inner_radius = 92
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.hide()

    def show_centered(self):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        size = 650
        self.setGeometry(geo.x() + (geo.width()-size)//2, geo.y() + (geo.height()-size)//2, size, size)
        self.items = self.controller.config["items"]
        self.mouse_pos = self.rect().center()
        self.selected = -1
        self.show()
        self.raise_()
        self.activateWindow()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            return
        if Qt.Key_1 <= event.key() <= Qt.Key_8:
            self.selected = event.key() - Qt.Key_1
            self.execute_selected()
            return

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.hide()
        elif event.button() == Qt.LeftButton:
            self.execute_selected()

    def calculate_selection(self):
        center = self.rect().center()
        dx = self.mouse_pos.x() - center.x()
        dy = self.mouse_pos.y() - center.y()
        distance = math.hypot(dx, dy)
        if distance < self.inner_radius * .7:
            return -1
        angle = (math.degrees(math.atan2(dy, dx)) + 90) % 360
        return int((angle + 22.5) // 45) % 8

    def execute_selected(self):
        if 0 <= self.selected < len(self.items):
            path = self.items[self.selected].get("path", "")
            if path:
                self.hide()
                launch(path)

    def paintEvent(self, event):
        self.selected = self.calculate_selection()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QPoint(self.width()//2, self.height()//2)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0,0,0,100))
        p.drawEllipse(c, self.radius+20, self.radius+20)

        for i in range(8):
            rect = QRectF(c.x()-self.radius, c.y()-self.radius, self.radius*2, self.radius*2)
            selected = i == self.selected
            p.setBrush(QColor(65,150,245,245) if selected else QColor(25,29,37,235))
            p.setPen(QPen(QColor(110,120,135,190), 2))
            start = 90*16 - i*45*16 - 22.5*16
            p.drawPie(rect, int(start), -45*16)

        p.setBrush(QColor(12,14,18,248))
        p.setPen(QPen(QColor(110,120,135,220), 2))
        p.drawEllipse(c, self.inner_radius, self.inner_radius)

        p.setPen(QColor(240,243,248))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        center_text = "Selecione um aplicativo" if self.selected < 0 else self.items[self.selected].get("name", "")
        p.drawText(QRectF(c.x()-85,c.y()-30,170,60), Qt.AlignCenter|Qt.TextWordWrap, center_text)

        for i, item in enumerate(self.items):
            a = math.radians(-90+i*45)
            d = self.radius*.69
            x, y = c.x()+math.cos(a)*d, c.y()+math.sin(a)*d
            name = item.get("name", f"Slot {i+1}") or f"Slot {i+1}"
            if len(name)>13: name=name[:12]+"…"
            p.setPen(QColor(245,247,250))
            p.setFont(QFont("Segoe UI", 9, QFont.Bold if i==self.selected else QFont.Normal))
            p.drawText(QRectF(x-65,y-18,130,36), Qt.AlignCenter|Qt.TextWordWrap, name)
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(185,195,210))
            p.drawText(QRectF(x-50,y+18,100,20), Qt.AlignCenter, str(i+1))


class Controller(QObject):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.settings = None
        self.hotkey_window = HotkeyWindow()
        self.hotkey_window.setWindowFlags(Qt.Tool)
        self.hotkey_window.resize(1,1)
        self.hotkey_window.move(-100,-100)
        self.hotkey_window.show()
        self.hotkey_window.hide()
        self.hotkey_window.hotkeyPressed.connect(self.toggle)

        self.launcher = RadialLauncher(self)

        self.tray = QSystemTrayIcon(self.make_icon(), QApplication.instance())
        menu = QMenu()
        act_open = menu.addAction("Abrir roda")
        act_open.triggered.connect(self.show_launcher)
        act_config = menu.addAction("Configurar")
        act_config.triggered.connect(self.show_settings)
        menu.addSeparator()
        act_quit = menu.addAction("Parar programa")
        act_quit.triggered.connect(self.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Radial Launcher")
        self.tray.show()

        self.apply_hotkey()

    def make_icon(self):
        if os.path.exists(ICON_FILE):
            return QIcon(ICON_FILE)
        px = QPixmap(64,64)
        px.fill(Qt.transparent)
        p=QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(65,150,245)); p.setPen(Qt.NoPen); p.drawEllipse(4,4,56,56)
        p.setPen(QColor(255,255,255)); p.setFont(QFont("Segoe UI",25,QFont.Bold))
        p.drawText(QRectF(0,0,64,64),Qt.AlignCenter,"R"); p.end()
        return QIcon(px)

    def apply_hotkey(self):
        user32.UnregisterHotKey(int(self.hotkey_window.winId()), HOTKEY_ID)
        hk = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"])
        mods = 0
        for m in hk.get("modifiers", []):
            mods |= {"win":MOD_WIN,"ctrl":MOD_CONTROL,"alt":MOD_ALT,"shift":MOD_SHIFT}.get(m,0)
        vk = KEYS.get(hk.get("key"))
        if not vk or not mods:
            return False
        return bool(user32.RegisterHotKey(int(self.hotkey_window.winId()), HOTKEY_ID, mods, vk))

    def reload_config(self):
        self.config = load_config()
        self.launcher.items = self.config["items"]

    def toggle(self):
        if self.launcher.isVisible():
            self.launcher.hide()
        else:
            self.reload_config()
            self.launcher.show_centered()

    def show_launcher(self):
        self.reload_config()
        self.launcher.show_centered()

    def show_settings(self):
        if self.settings and self.settings.isVisible():
            self.settings.raise_()
            self.settings.activateWindow()
            return
        self.settings = SettingsDialog(self)
        self.settings.show()

    def quit(self):
        user32.UnregisterHotKey(int(self.hotkey_window.winId()), HOTKEY_ID)
        self.tray.hide()
        QApplication.quit()


def main():
    if sys.platform != "win32":
        print("Este aplicativo foi feito para Windows.")
        return
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    controller = Controller()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

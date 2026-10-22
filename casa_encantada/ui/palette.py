"""Paleta lateral: todas las piezas del nivel, arrastrables al tablero."""
from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ..logic.elements import CATEGORY_CODES, CATEGORY_NAMES, describe
from .board import GROUP_ORDER, MIME

ICON = 46


class PaletteItem(QLabel):
    def __init__(self, code, images, parent=None):
        super().__init__(parent)
        self.code, self.images = code, images
        self.setFixedSize(ICON + 8, ICON + 8)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip(describe(code) + "\n(arrastra a una casilla)")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.refresh()

    def refresh(self):
        self.setPixmap(self.images.pixmap(self.code).scaled(
            ICON, ICON, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME, f"{self.code};-1;-1".encode())
        drag.setMimeData(mime)
        pm = self.pixmap()
        drag.setPixmap(pm)
        drag.setHotSpot(QPoint(pm.width() // 2, pm.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)


class PaletteWidget(QWidget):
    def __init__(self, images, parent=None):
        super().__init__(parent)
        self.images = images
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.titles = {}
        self.items = []
        self.level = None
        self.show_counts = True

    def setup(self, level, show_counts=True):
        self.level, self.show_counts = level, show_counts
        while self.root.count():
            w = self.root.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.titles.clear()
        self.items.clear()
        for cat in GROUP_ORDER:
            if cat not in level.counts:
                continue
            title = QLabel()
            title.setStyleSheet("font-weight: bold;")
            self.titles[cat] = title
            self.root.addWidget(title)
            holder = QWidget()
            grid = QGridLayout(holder)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(2)
            for k, code in enumerate(CATEGORY_CODES[cat]):
                item = PaletteItem(code, self.images)
                self.items.append(item)
                grid.addWidget(item, k // 4, k % 4)
            self.root.addWidget(holder)
        hint = QLabel("Clic: cambia de pieza · Clic derecho: gira el espejo\n"
                      "Arrastra una pieza fuera del tablero para quitarla")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 10px;")
        self.root.addWidget(hint)
        self.root.addStretch(1)
        self.update_counts({})

    def refresh_images(self):
        for it in self.items:
            it.refresh()

    def update_counts(self, placed):
        if not self.level:
            return
        for cat, title in self.titles.items():
            need, have = self.level.counts[cat], placed.get(cat, 0)
            if self.show_counts:
                color = "#ef4444" if have > need else ("#22c55e" if have == need else "")
                title.setText(f"{CATEGORY_NAMES[cat]}: {have}/{need}")
                title.setStyleSheet(f"font-weight: bold; color: {color};" if color
                                    else "font-weight: bold;")
            else:
                title.setText(CATEGORY_NAMES[cat])
                title.setStyleSheet("font-weight: bold;")

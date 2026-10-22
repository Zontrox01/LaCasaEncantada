"""Carga de gráficos desde assets/img (editables por el usuario)."""
from PySide6.QtGui import QPixmap

from ..config import IMG_DIR
from ..logic.elements import element_key


class ImageStore:
    def __init__(self):
        self.cache = {}

    def pixmap(self, code: int) -> QPixmap:
        pm = self.cache.get(code)
        if pm is None:
            pm = QPixmap(str(IMG_DIR / f"{element_key(code)}.png"))
            self.cache[code] = pm
        return pm

    def reload(self):
        self.cache.clear()

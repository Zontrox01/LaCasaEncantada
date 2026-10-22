"""Tablero: cuadrícula n x n rodeada de los 4n marcadores numéricos."""
from collections import Counter

from PySide6.QtCore import QMimeData, QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from ..logic.elements import (CAT_BLOCK, CAT_GHOST, CAT_MIRROR1, CAT_MIRROR2,
                              CAT_VAMPIRE, CAT_ZOMBIE, CATEGORY_CODES, EMPTY,
                              category_of)

MIME = "application/x-casa-encantada"
GROUP_ORDER = [CAT_ZOMBIE, CAT_VAMPIRE, CAT_GHOST, CAT_MIRROR2, CAT_MIRROR1, CAT_BLOCK]

THEMES = {
    "oscuro": dict(bg="#1d1d22", floor="#2a2a31", wall="#c2410c", lcd_bg="#06141b",
                   lcd_fg="#22e5ff", lcd_border="#3a6f80", hover="#ffffff30"),
    "claro": dict(bg="#d9d6cc", floor="#efece3", wall="#b45309", lcd_bg="#06141b",
                  lcd_fg="#22e5ff", lcd_border="#4b6b78", hover="#00000025"),
}


class BoardWidget(QWidget):
    changed = Signal()          # el usuario modificó la cuadrícula
    placed = Signal(int)        # código del elemento colocado/cambiado (EMPTY = quitado)

    def __init__(self, images, parent=None):
        super().__init__(parent)
        self.images = images
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setMinimumSize(380, 380)
        self.theme = THEMES["oscuro"]
        self.n = 3
        self.targets = [0] * 12
        self.grid = [[EMPTY] * 3 for _ in range(3)]
        self.locked = set()      # pistas fijas
        self.hinted = set()      # celdas reveladas por una pista del juego
        self.bad = set()         # índices de marcadores erróneos
        self.good = set()        # índices de marcadores correctos (tras comprobar)
        self.groups = [[EMPTY]]
        self.undo_stack, self.redo_stack = [], []
        self.readonly = True
        self.hover = None
        self._press = None

    # ------------------------------------------------------------ configuración
    def set_theme(self, name):
        self.theme = THEMES.get(name, THEMES["oscuro"])
        self.update()

    def setup(self, puzzle, level):
        self.n = puzzle.size
        self.targets = list(puzzle.numbers)
        self.grid = [[EMPTY] * self.n for _ in range(self.n)]
        self.locked = set(puzzle.fixed)
        for (r, c), code in puzzle.fixed.items():
            self.grid[r][c] = code
        self.hinted = set()
        self.groups = [[EMPTY]] + [CATEGORY_CODES[c] for c in GROUP_ORDER if c in level.counts]
        self.undo_stack, self.redo_stack = [], []
        self.clear_marks()
        self.readonly = False
        self.update()

    def clear_marks(self):
        self.bad, self.good = set(), set()

    def set_marks(self, bad, good):
        self.bad, self.good = set(bad), set(good)
        self.update()

    def counts(self):
        cnt = Counter()
        for row in self.grid:
            for code in row:
                cat = category_of(code)
                if cat:
                    cnt[cat] += 1
        return cnt

    # ------------------------------------------------------------ edición
    def apply_changes(self, changes, record=True):
        """changes: lista de (fila, col, anterior, nuevo)."""
        changes = [ch for ch in changes if ch[2] != ch[3]]
        if not changes:
            return
        for r, c, _old, new in changes:
            self.grid[r][c] = new
        if record:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
        self.clear_marks()
        self.update()
        self.changed.emit()
        self.placed.emit(changes[-1][3])

    def undo(self):
        if self.undo_stack and not self.readonly:
            changes = self.undo_stack.pop()
            for r, c, old, _new in changes:
                self.grid[r][c] = old
            self.redo_stack.append(changes)
            self.clear_marks()
            self.update()
            self.changed.emit()

    def redo(self):
        if self.redo_stack and not self.readonly:
            changes = self.redo_stack.pop()
            for r, c, _old, new in changes:
                self.grid[r][c] = new
            self.undo_stack.append(changes)
            self.clear_marks()
            self.update()
            self.changed.emit()

    def clear_all(self):
        """Quita todas las piezas no fijas (una sola acción deshacible)."""
        changes = [(r, c, self.grid[r][c], EMPTY) for r in range(self.n)
                   for c in range(self.n)
                   if (r, c) not in self.locked and self.grid[r][c] != EMPTY]
        self.apply_changes(changes)

    def show_solution(self, solution):
        self.grid = [row[:] for row in solution]
        self.readonly = True
        self.clear_marks()
        self.update()

    def reveal_hint(self, solution):
        """Coloca una celda correcta. Devuelve True si hubo alguna que revelar."""
        wrong = [(r, c) for r in range(self.n) for c in range(self.n)
                 if (r, c) not in self.locked and self.grid[r][c] != solution[r][c]]
        if not wrong:
            return False
        import random
        r, c = random.choice(wrong)
        self.apply_changes([(r, c, self.grid[r][c], solution[r][c])])
        self.locked.add((r, c))
        self.hinted.add((r, c))
        self.update()
        return True

    def _cycle_group(self, cell, step):
        r, c = cell
        if cell in self.locked:
            return
        cur = self.grid[r][c]
        gi = next((i for i, g in enumerate(self.groups) if cur in g), 0)
        new = self.groups[(gi + step) % len(self.groups)][0]
        self.apply_changes([(r, c, cur, new)])

    def _rotate_variant(self, cell):
        r, c = cell
        if cell in self.locked:
            return
        cur = self.grid[r][c]
        group = next((g for g in self.groups if cur in g), None)
        if group and len(group) > 1:
            new = group[(group.index(cur) + 1) % len(group)]
            self.apply_changes([(r, c, cur, new)])

    # ------------------------------------------------------------ geometría
    def _metrics(self):
        cell = min(self.width(), self.height()) / (self.n + 2)
        ox = (self.width() - cell * (self.n + 2)) / 2
        oy = (self.height() - cell * (self.n + 2)) / 2
        return cell, ox, oy

    def _cell_at(self, pos):
        cell, ox, oy = self._metrics()
        c = int((pos.x() - ox) // cell) - 1
        r = int((pos.y() - oy) // cell) - 1
        if 0 <= r < self.n and 0 <= c < self.n:
            return r, c
        return None

    def _number_pos(self, i):
        """Posición (columna, fila) en la rejilla (n+2)x(n+2) del marcador i."""
        n = self.n
        if i < n:
            return i + 1, 0
        if i < 2 * n:
            return i - n + 1, n + 1
        if i < 3 * n:
            return 0, i - 2 * n + 1
        return n + 1, i - 3 * n + 1

    # ------------------------------------------------------------ pintado
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        t = self.theme
        p.fillRect(self.rect(), QColor(t["bg"]))
        cell, ox, oy = self._metrics()
        n = self.n
        # suelo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(t["floor"]))
        p.drawRoundedRect(QRectF(ox + cell, oy + cell, cell * n, cell * n), 8, 8)
        # paredes de lava (rejilla)
        pen = QPen(QColor(t["wall"]), max(2.0, cell * 0.05))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for k in range(n + 1):
            x = ox + (k + 1) * cell
            y = oy + (k + 1) * cell
            p.drawLine(int(x), int(oy + cell), int(x), int(oy + (n + 1) * cell))
            p.drawLine(int(ox + cell), int(y), int(ox + (n + 1) * cell), int(y))
        # piezas
        m = cell * 0.08
        for r in range(n):
            for c in range(n):
                rect = QRectF(ox + (c + 1) * cell + m, oy + (r + 1) * cell + m,
                              cell - 2 * m, cell - 2 * m)
                p.drawPixmap(rect, self.images.pixmap(self.grid[r][c]),
                             QRectF(self.images.pixmap(self.grid[r][c]).rect()))
                if (r, c) in self.hinted:
                    p.setPen(QPen(QColor("#facc15"), 3))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(rect, 6, 6)
                elif (r, c) in self.locked:
                    p.setPen(QPen(QColor("#94a3b8"), 3, Qt.PenStyle.DashLine))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(rect, 6, 6)
        if self.hover and not self.readonly:
            r, c = self.hover
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["hover"]))
            p.drawRect(QRectF(ox + (c + 1) * cell, oy + (r + 1) * cell, cell, cell))
        # marcadores numéricos
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setBold(True)
        font.setPixelSize(max(10, int(cell * 0.45)))
        p.setFont(font)
        for i, val in enumerate(self.targets):
            col, row = self._number_pos(i)
            rect = QRectF(ox + col * cell + cell * 0.12, oy + row * cell + cell * 0.12,
                          cell * 0.76, cell * 0.76)
            border, fg = QColor(t["lcd_border"]), QColor(t["lcd_fg"])
            if i in self.bad:
                border, fg = QColor("#ef4444"), QColor("#ff6b6b")
            elif i in self.good:
                border, fg = QColor("#22c55e"), QColor("#4ade80")
            p.setPen(QPen(border, max(2.0, cell * 0.04)))
            p.setBrush(QColor("#3a0b0b") if i in self.bad else QColor(t["lcd_bg"]))
            p.drawRoundedRect(rect, 6, 6)
            p.setPen(fg)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{val:02d}")
        p.end()

    # ------------------------------------------------------------ ratón
    def mousePressEvent(self, e):
        if self.readonly:
            return
        pos = e.position().toPoint()
        cell = self._cell_at(pos)
        if cell is None:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = (cell, pos)
        elif e.button() == Qt.MouseButton.RightButton:
            self._rotate_variant(cell)
        elif e.button() == Qt.MouseButton.MiddleButton:
            self._cycle_group(cell, -1)

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        hov = self._cell_at(pos)
        if hov != self.hover:
            self.hover = hov
            self.update()
        if self._press and (e.buttons() & Qt.MouseButton.LeftButton):
            (r, c), p0 = self._press
            if (pos - p0).manhattanLength() >= QApplication.startDragDistance():
                self._press = None
                if (r, c) not in self.locked and self.grid[r][c] != EMPTY:
                    self._start_drag(r, c)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._press and not self.readonly:
            cell, _p0 = self._press
            if self._cell_at(e.position().toPoint()) == cell:
                step = -1 if (e.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1
                self._cycle_group(cell, step)
        self._press = None

    def leaveEvent(self, _e):
        self.hover = None
        self.update()

    def wheelEvent(self, e):
        if self.readonly:
            return
        cell = self._cell_at(e.position().toPoint())
        if cell is not None:
            self._cycle_group(cell, 1 if e.angleDelta().y() < 0 else -1)

    def _start_drag(self, r, c):
        code = self.grid[r][c]
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME, f"{code};{r};{c}".encode())
        drag.setMimeData(mime)
        cell, _, _ = self._metrics()
        pm = self.images.pixmap(code).scaled(int(cell * 0.8), int(cell * 0.8),
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        drag.setPixmap(pm)
        drag.setHotSpot(QPoint(pm.width() // 2, pm.height() // 2))
        result = drag.exec(Qt.DropAction.MoveAction)
        if result == Qt.DropAction.IgnoreAction and not self.readonly:
            # soltado fuera del tablero: se quita la pieza
            self.apply_changes([(r, c, self.grid[r][c], EMPTY)])

    # ------------------------------------------------------------ arrastrar y soltar
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(MIME) and not self.readonly:
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(MIME) and not self.readonly:
            hov = self._cell_at(e.position().toPoint())
            if hov != self.hover:
                self.hover = hov
                self.update()
            e.acceptProposedAction()

    def dropEvent(self, e):
        if not e.mimeData().hasFormat(MIME) or self.readonly:
            return
        cell = self._cell_at(e.position().toPoint())
        if cell is None or cell in self.locked:
            e.acceptProposedAction()     # soltado dentro del tablero pero sin efecto
            return
        try:
            code, sr, sc = (int(x) for x in
                            e.mimeData().data(MIME).data().decode().split(";"))
        except ValueError:
            return
        r, c = cell
        changes = []
        if sr >= 0 and (sr, sc) == (r, c):
            e.acceptProposedAction()
            return
        if sr >= 0:
            changes.append((sr, sc, self.grid[sr][sc], EMPTY))
        changes.append((r, c, self.grid[r][c], code))
        self.apply_changes(changes)
        self.hover = None
        e.acceptProposedAction()

"""Genera los gráficos y sonidos por defecto SI NO EXISTEN.

Todos los gráficos son PNG de 160x160 en assets/img/. Para cambiar uno,
basta con sustituir el archivo por el tuyo (mismo nombre). Si borras un
archivo, se regenerará el original la próxima vez que arranque el juego.
"""
import math
import struct
import wave
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPolygonF)

from .logic.elements import (ALL_CODES, BLOCK, EMPTY, GHOST,
                             MIRROR2_BACKSLASH, MIRROR2_SLASH, VAMPIRE, ZOMBIE,
                             element_key, mirror1_parts)

S = 160
_R2 = math.sqrt(2)
# Normales de cada cara (coordenadas de pantalla: y hacia abajo)
_NORMALS = {(0, 0): (-1, -1), (0, 1): (1, 1), (1, 0): (-1, 1), (1, 1): (1, -1)}


def _c(h, a=255):
    col = QColor(h)
    col.setAlpha(a)
    return col


def _draw_empty(p):
    g = QLinearGradient(0, 0, S, S)
    g.setColorAt(0, _c("#e6e6e6"))
    g.setColorAt(1, _c("#9a9a9a"))
    p.setBrush(QBrush(g))
    p.setPen(QPen(_c("#555555"), 3))
    p.drawRoundedRect(QRectF(26, 26, S - 52, S - 52), 6, 6)
    p.setPen(QPen(_c("#ffffff", 160), 2))
    p.drawLine(30, 30, S - 30, 30)
    p.drawLine(30, 30, 30, S - 30)


def _draw_block(p):
    p.setBrush(_c("#3a3a44"))
    p.setPen(QPen(_c("#15151a"), 4))
    p.drawRoundedRect(QRectF(14, 14, S - 28, S - 28), 8, 8)
    p.setPen(QPen(_c("#5b5b68"), 2))
    for y in (50, 80, 110):
        p.drawLine(18, y, S - 18, y)
    for y, xs in ((50, (60, 110)), (80, (40, 90, 130)), (110, (70,))):
        for x in xs:
            p.drawLine(x, y, x, y + 30 if y < 110 else y + 28)
    p.setPen(QPen(_c("#c0392b"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(48, 48, S - 48, S - 48)
    p.drawLine(S - 48, 48, 48, S - 48)


def _draw_zombie(p):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#4b5a6e"))                       # hombros / ropa rota
    p.drawRoundedRect(QRectF(26, 112, 108, 40), 14, 14)
    p.setBrush(_c("#7fb05b"))
    p.setPen(QPen(_c("#2f4a1d"), 4))
    p.drawEllipse(QRectF(36, 18, 88, 100))          # cabeza
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#2b2b2b"))
    p.drawChord(QRectF(36, 18, 88, 70), 20 * 16, 140 * 16)   # pelo
    p.setBrush(_c("#ffffff"))
    p.setPen(QPen(_c("#222222"), 2))
    p.drawEllipse(QRectF(50, 52, 24, 24))
    p.drawEllipse(QRectF(88, 56, 18, 18))
    p.setBrush(_c("#b0121a"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(58, 60, 9, 9))
    p.drawEllipse(QRectF(93, 62, 8, 8))
    p.setPen(QPen(_c("#3b1d1d"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(56, 94, 108, 98)                     # boca cosida
    p.setPen(QPen(_c("#3b1d1d"), 2))
    for x in range(62, 108, 10):
        p.drawLine(x, 89, x + 2, 104)


def _draw_vampire(p):
    p.setPen(Qt.PenStyle.NoPen)
    cape = QPolygonF([QPointF(10, 150), QPointF(34, 70), QPointF(126, 70), QPointF(150, 150)])
    p.setBrush(_c("#7a0d1a"))
    p.drawPolygon(cape)
    p.setBrush(_c("#1a1a22"))                       # cuello alto
    p.drawPolygon(QPolygonF([QPointF(40, 80), QPointF(60, 120), QPointF(80, 100),
                             QPointF(100, 120), QPointF(120, 80), QPointF(120, 140),
                             QPointF(40, 140)]))
    p.setBrush(_c("#ece6ea"))
    p.setPen(QPen(_c("#4a4a55"), 3))
    p.drawEllipse(QRectF(42, 16, 76, 90))           # cara
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#111118"))
    path = QPainterPath()                           # pelo con pico
    path.moveTo(40, 58)
    path.lineTo(80, 38)
    path.lineTo(120, 58)
    path.cubicTo(120, 10, 40, 10, 40, 58)
    p.drawPath(path)
    p.setBrush(_c("#e01b24"))
    p.drawEllipse(QRectF(56, 62, 14, 12))
    p.drawEllipse(QRectF(90, 62, 14, 12))
    p.setBrush(_c("#5a0b10"))
    p.drawChord(QRectF(60, 78, 40, 22), 180 * 16, 180 * 16)
    p.setBrush(_c("#ffffff"))
    p.drawPolygon(QPolygonF([QPointF(66, 88), QPointF(74, 88), QPointF(70, 102)]))
    p.drawPolygon(QPolygonF([QPointF(86, 88), QPointF(94, 88), QPointF(90, 102)]))


def _draw_ghost(p):
    path = QPainterPath()
    path.moveTo(36, 140)
    path.lineTo(36, 70)
    path.cubicTo(36, 8, 124, 8, 124, 70)
    path.lineTo(124, 140)
    path.quadTo(112, 120, 102, 140)
    path.quadTo(92, 120, 80, 140)
    path.quadTo(68, 120, 58, 140)
    path.quadTo(48, 120, 36, 140)
    g = QLinearGradient(0, 10, 0, 140)
    g.setColorAt(0, _c("#ffffff", 245))
    g.setColorAt(1, _c("#b9d9ff", 215))
    p.setBrush(QBrush(g))
    p.setPen(QPen(_c("#6a8fb8"), 3))
    p.drawPath(path)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#1b2230"))
    p.drawEllipse(QRectF(54, 54, 18, 26))
    p.drawEllipse(QRectF(88, 54, 18, 26))
    p.drawEllipse(QRectF(72, 92, 16, 20))


def _strip(p, a, b, nx, ny, t, fill, edge):
    n = math.hypot(nx, ny)
    ox, oy = nx / n * t, ny / n * t
    poly = QPolygonF([QPointF(*a), QPointF(*b),
                      QPointF(b[0] + ox, b[1] + oy), QPointF(a[0] + ox, a[1] + oy)])
    p.setBrush(fill)
    p.setPen(QPen(edge, 2))
    p.drawPolygon(poly)
    return poly


def _mirror_line(diag):
    m = 20
    return ((m, S - m), (S - m, m)) if diag == 0 else ((m, m), (S - m, S - m))


def _reflective_fill(a, b):
    g = QLinearGradient(a[0], a[1], b[0], b[1])
    g.setColorAt(0, _c("#8fd3ff"))
    g.setColorAt(0.5, _c("#f4fcff"))
    g.setColorAt(1, _c("#6cb8f0"))
    return QBrush(g)


def _draw_mirror2(p, diag):
    a, b = _mirror_line(diag)
    n1, n2 = _NORMALS[(diag, 0)], _NORMALS[(diag, 1)]
    _strip(p, a, b, n1[0], n1[1], 13, _reflective_fill(a, b), _c("#2d6a99"))
    _strip(p, a, b, n2[0], n2[1], 13, _reflective_fill(a, b), _c("#2d6a99"))


def _draw_mirror1(p, code):
    diag, face, back = mirror1_parts(code)
    a, b = _mirror_line(diag)
    nr = _NORMALS[(diag, face)]
    nb = _NORMALS[(diag, 1 - face)]
    _strip(p, a, b, nr[0], nr[1], 13, _reflective_fill(a, b), _c("#2d6a99"))
    if back == 0:
        _strip(p, a, b, nb[0], nb[1], 13, _c("#ffffff"), _c("#8a8a8a"))
    else:
        _strip(p, a, b, nb[0], nb[1], 13, _c("#101010"), _c("#000000"))


def draw_element(code):
    img = QImage(S, S, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if code == EMPTY:
        _draw_empty(p)
    elif code == BLOCK:
        _draw_block(p)
    elif code == ZOMBIE:
        _draw_zombie(p)
    elif code == VAMPIRE:
        _draw_vampire(p)
    elif code == GHOST:
        _draw_ghost(p)
    elif code == MIRROR2_SLASH:
        _draw_mirror2(p, 0)
    elif code == MIRROR2_BACKSLASH:
        _draw_mirror2(p, 1)
    else:
        _draw_mirror1(p, code)
    p.end()
    return img


def ensure_default_images(img_dir: Path, overwrite=False):
    img_dir.mkdir(parents=True, exist_ok=True)
    for code in ALL_CODES:
        path = img_dir / f"{element_key(code)}.png"
        if overwrite or not path.exists():
            draw_element(code).save(str(path), "PNG")


# ------------------------------------------------------------------ sonidos
def _write_wav(path: Path, notes, volume=0.4, rate=22050):
    """notes: lista de (frecuencia_hz, duracion_s)."""
    frames = bytearray()
    for freq, dur in notes:
        n = int(rate * dur)
        for i in range(n):
            env = min(1.0, i / 200, (n - i) / 400)
            v = math.sin(2 * math.pi * freq * i / rate) * volume * env
            frames += struct.pack("<h", int(v * 32767))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def ensure_default_sfx(sfx_dir: Path):
    sfx_dir.mkdir(parents=True, exist_ok=True)
    defaults = {
        "click.wav": [(880, 0.04)],
        "place.wav": [(520, 0.05), (660, 0.05)],
        "zombi.wav": [(150, 0.10), (120, 0.10), (95, 0.16)],
        "vampiro.wav": [(900, 0.06), (700, 0.06), (900, 0.12)],
        "fantasma.wav": [(500, 0.07), (620, 0.07), (500, 0.07), (620, 0.09)],
        "espejo.wav": [(1320, 0.03), (1760, 0.10)],
        "bloque.wav": [(80, 0.14)],
        "vacio.wav": [(400, 0.04)],
        "win.wav": [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.3)],
        "lose.wav": [(330, 0.18), (262, 0.18), (196, 0.35)],
    }
    for name, notes in defaults.items():
        path = sfx_dir / name
        if not path.exists():
            _write_wav(path, notes)

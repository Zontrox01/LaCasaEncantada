"""Diálogos: opciones, estadísticas, ayuda y acerca de."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QFormLayout, QHBoxLayout, QPushButton,
                               QSlider, QTableWidget, QTableWidgetItem,
                               QTextBrowser, QVBoxLayout)

from .. import __version__
from ..config import Settings, fmt_time
from ..logic.elements import LEVELS, LEVEL_ORDER


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones")
        self.s = settings
        form = QFormLayout()
        self.level = QComboBox()
        for k in LEVEL_ORDER:
            self.level.addItem(LEVELS[k].name, k)
        self.level.setCurrentIndex(LEVEL_ORDER.index(settings.level))
        form.addRow("Nivel (próxima partida):", self.level)
        self.full = QCheckBox("Pantalla completa (F11)")
        self.full.setChecked(settings.fullscreen)
        form.addRow(self.full)
        self.theme = QComboBox()
        self.theme.addItems(["oscuro", "claro"])
        self.theme.setCurrentText(settings.theme)
        form.addRow("Tema:", self.theme)

        self.music = QCheckBox("Música de fondo")
        self.music.setChecked(settings.music_on)
        self.mvol = self._slider(settings.music_volume)
        form.addRow(self.music)
        form.addRow("Volumen música:", self.mvol)
        self.sfx = QCheckBox("Efectos de sonido")
        self.sfx.setChecked(settings.sfx_on)
        self.svol = self._slider(settings.sfx_volume)
        form.addRow(self.sfx)
        form.addRow("Volumen efectos:", self.svol)

        self.wrong = QCheckBox("Resaltar los números erróneos al comprobar")
        self.wrong.setChecked(settings.highlight_wrong)
        self.timer = QCheckBox("Mostrar cronómetro")
        self.timer.setChecked(settings.show_timer)
        self.counts = QCheckBox("Mostrar contadores de piezas (colocadas/necesarias)")
        self.counts.setChecked(settings.show_counts)
        for w in (self.wrong, self.timer, self.counts):
            form.addRow(w)

        self.btn_assets = QPushButton("Abrir carpeta de recursos (gráficos, música, sonidos)")
        self.btn_restore = QPushButton("Restaurar gráficos originales")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self.btn_assets)
        lay.addWidget(self.btn_restore)
        lay.addWidget(buttons)

    @staticmethod
    def _slider(value):
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(0, 100)
        sl.setValue(value)
        return sl

    def apply_to(self, s: Settings):
        s.level = self.level.currentData()
        s.fullscreen = self.full.isChecked()
        s.theme = self.theme.currentText()
        s.music_on, s.music_volume = self.music.isChecked(), self.mvol.value()
        s.sfx_on, s.sfx_volume = self.sfx.isChecked(), self.svol.value()
        s.highlight_wrong = self.wrong.isChecked()
        s.show_timer = self.timer.isChecked()
        s.show_counts = self.counts.isChecked()


class StatsDialog(QDialog):
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estadísticas")
        self.stats = stats
        self.table = QTableWidget(len(LEVEL_ORDER), 6)
        self.table.setHorizontalHeaderLabels(
            ["Nivel", "Jugadas", "Ganadas", "Rendidas", "Mejor tiempo", "Tiempo medio"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reset_btn = QPushButton("Borrar estadísticas")
        self.reset_btn.clicked.connect(self._reset)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addWidget(self.reset_btn)
        row.addStretch(1)
        row.addWidget(close)
        lay = QVBoxLayout(self)
        lay.addWidget(self.table)
        lay.addLayout(row)
        self.resize(640, 220)
        self._fill()

    def _fill(self):
        for i, key in enumerate(LEVEL_ORDER):
            d = self.stats.level(key)
            avg = fmt_time(d["total_time"] / d["won"]) if d["won"] else "-"
            best = fmt_time(d["best"]) if d["best"] is not None else "-"
            vals = [LEVELS[key].name, d["played"], d["won"], d["gave_up"], best, avg]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(str(v)))
        self.table.resizeColumnsToContents()

    def _reset(self):
        self.stats.reset()
        self._fill()


HELP_HTML = """
<h2>La casa encantada</h2>
<p>Cada casilla del tablero contiene <b>una pieza</b>. Los números del borde indican
cuántos monstruos se ven al mirar <b>desde ese lado hacia dentro</b> (la mirada
atraviesa las filas y columnas, y rebota en los espejos). Coloca las piezas para que
<b>todos</b> los números coincidan.</p>
<h3>Qué se ve</h3>
<ul>
<li><b>Zombi</b>: se ve siempre, directo o reflejado.</li>
<li><b>Vampiro</b>: solo se ve <i>antes</i> de reflejarse; nunca en un espejo.</li>
<li><b>Fantasma</b>: solo se ve <i>después</i> de reflejarse al menos una vez.</li>
<li>Los monstruos <b>no bloquean</b> la vista. Si la mirada pasa dos veces por el mismo
monstruo (ida y vuelta), se cuenta dos veces.</li>
<li><b>Espejo de doble cara</b> (<tt>/</tt> o <tt>\\</tt>): refleja por ambos lados.</li>
<li><b>Espejo de una cara</b>: solo refleja por la cara plateada. La otra cara es
<b>blanca</b> (la mirada la atraviesa como si no hubiera nada) o <b>negra</b>
(la mirada se detiene).</li>
<li><b>Bloque</b>: opaco, la mirada muere ahí.</li>
<li>Si con espejos de una cara la mirada entra en un circuito cerrado, se detiene al
volver a pasar por la misma casilla en la misma dirección.</li>
</ul>
<h3>Controles</h3>
<ul>
<li><b>Clic izquierdo</b>: siguiente pieza (<b>Mayús+clic</b> o rueda arriba: anterior).</li>
<li><b>Clic derecho</b>: gira / cambia la variante del espejo.</li>
<li><b>Arrastrar</b> desde la paleta a una casilla; arrastra una pieza del tablero para
moverla o suéltala fuera para quitarla.</li>
<li><b>Ctrl+Z / Ctrl+Y</b>: deshacer / rehacer · <b>F11</b>: pantalla completa.</li>
<li>Las casillas con borde discontinuo son pistas fijas; con borde amarillo, ayudas
del botón <i>Pista</i>.</li>
</ul>
<h3>Niveles</h3>
<ul>
<li><b>Fácil 3x3</b>: 3 espejos de doble cara, 3 zombis y 3 vampiros.</li>
<li><b>Normal 4x4</b>: 4 espejos de doble cara, 4 zombis, 4 vampiros y 4 fantasmas.</li>
<li><b>Difícil 5x5</b>: lo anterior más 5 espejos de una cara y 4 bloques. Puede tener
varias soluciones: vale cualquiera que cumpla todos los números.</li>
</ul>
<p>Los gráficos, la música y los sonidos están en la carpeta <tt>assets/</tt>: puedes
sustituirlos por los tuyos.</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda")
        view = QTextBrowser()
        view.setHtml(HELP_HTML)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addWidget(view)
        lay.addWidget(close)
        self.resize(560, 620)


ABOUT_TEXT = (f"<b>La casa encantada</b> v{__version__}<br>"
              "Juego de lógica con espejos, zombis, vampiros y fantasmas.<br>"
              "Hecho con Python y PySide6.")

"""Ventana principal."""
import random

from PySide6.QtCore import QThread, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QProgressDialog, QPushButton, QVBoxLayout, QWidget)

from ..assets_gen import ensure_default_images
from ..config import ASSETS_DIR, IMG_DIR, Settings, Stats, fmt_time
from ..logic.elements import (CAT_BLOCK, CAT_GHOST, CAT_MIRROR1, CAT_MIRROR2,
                              CAT_VAMPIRE, CAT_ZOMBIE, LEVELS, category_of)
from ..logic.generator import generate
from ..logic.raytrace import compute_numbers
from .board import BoardWidget
from .dialogs import ABOUT_TEXT, HelpDialog, SettingsDialog, StatsDialog
from .images import ImageStore
from .palette import PaletteWidget

# Nombre del archivo de sonido (assets/sfx/<nombre>.wav) según el elemento colocado
SFX_BY_CATEGORY = {CAT_ZOMBIE: "zombi", CAT_VAMPIRE: "vampiro", CAT_GHOST: "fantasma",
                   CAT_MIRROR2: "espejo", CAT_MIRROR1: "espejo", CAT_BLOCK: "bloque"}

QSS = {
    "oscuro": """
        QWidget { background: #26262c; color: #e5e5ea; }
        QPushButton { background: #3a3a44; border: 1px solid #55555f; border-radius: 4px; padding: 6px; }
        QPushButton:hover { background: #4a4a58; }
        QPushButton:disabled { color: #777; background: #2e2e35; }
        QToolTip { color: #111; background: #ffffe0; }
    """,
    "claro": """
        QWidget { background: #ebe8df; color: #1c1c1c; }
        QPushButton { background: #f7f5ee; border: 1px solid #aaa; border-radius: 4px; padding: 6px; }
        QPushButton:hover { background: #fff; }
        QPushButton:disabled { color: #999; }
        QToolTip { color: #111; background: #ffffe0; }
    """,
}


class GeneratorThread(QThread):
    progress = Signal(str)
    ready = Signal(object)

    def __init__(self, level, parent=None):
        super().__init__(parent)
        self.level = level
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            puzzle = generate(self.level, random.Random(), progress=self.progress.emit,
                              cancel=lambda: self._cancel)
        except InterruptedError:
            return
        if not self._cancel:
            self.ready.emit(puzzle)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, stats: Stats, audio, images: ImageStore):
        super().__init__()
        self.setWindowTitle("La casa encantada")
        self.settings, self.stats, self.audio, self.images = settings, stats, audio, images
        self.puzzle = None
        self.level = LEVELS[settings.level]
        self.seconds = 0
        self.hints = 0
        self.attempts = 0
        self.finished = True
        self.gen = None
        self.dialog = None

        self.board = BoardWidget(images)
        self.palette = PaletteWidget(images)
        self.board.changed.connect(self._on_board_changed)
        self.board.placed.connect(self._on_placed)

        self.lbl_time = QLabel("0h 0m 0s")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet(
            "color: #22c55e; font: bold 20px 'Consolas', monospace; background: transparent;")
        self.lbl_level = QLabel()
        self.lbl_level.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_info = QLabel()
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("font-size: 11px;")

        def btn(text, slot, tip=None):
            b = QPushButton(text)
            b.clicked.connect(slot)
            if tip:
                b.setToolTip(tip)
            return b

        self.btn_new = btn("Empezar juego nuevo", self.new_game)
        self.btn_giveup = btn("Me rindo", self.give_up, "Muestra la solución")
        self.btn_check = btn("Comprobar jugada", self.check_play)
        self.btn_hint = btn("Pista", self.hint, "Revela una casilla correcta")
        self.btn_undo = btn("Deshacer", self.board.undo)
        self.btn_redo = btn("Rehacer", self.board.redo)
        self.btn_clear = btn("Reiniciar casillas", self.clear_board, "Quita todas las piezas")
        self.btn_music = btn("Quitar música", self.toggle_music)
        self.btn_settings = btn("Opciones...", self.open_settings)
        self.btn_stats = btn("Estadísticas...", lambda: StatsDialog(self.stats, self).exec())
        self.btn_help = btn("Ayuda", lambda: HelpDialog(self).exec())
        self.btn_about = btn("Acerca de...",
                             lambda: QMessageBox.about(self, "Acerca de", ABOUT_TEXT))
        self.btn_exit = btn("Salir del juego", self.close)

        side = QVBoxLayout()
        side.addWidget(self.lbl_time)
        side.addWidget(self.lbl_level)
        side.addWidget(self.lbl_info)
        side.addWidget(self.palette, 1)
        for b in (self.btn_new, self.btn_giveup, self.btn_check):
            side.addWidget(b)
        row = QHBoxLayout()
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_redo)
        side.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(self.btn_hint)
        row2.addWidget(self.btn_clear)
        side.addLayout(row2)
        for b in (self.btn_music, self.btn_settings, self.btn_stats, self.btn_help,
                  self.btn_about, self.btn_exit):
            side.addWidget(b)
        panel = QWidget()
        panel.setLayout(side)
        panel.setFixedWidth(270)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.addWidget(self.board, 1)
        lay.addWidget(panel)
        self.setCentralWidget(central)
        self.resize(900, 620)

        self.clock = QTimer(self)
        self.clock.setInterval(1000)
        self.clock.timeout.connect(self._tick)

        for seq, slot in (("Ctrl+Z", self.board.undo), ("Ctrl+Y", self.board.redo),
                          ("Ctrl+N", self.new_game), ("F11", self.toggle_fullscreen)):
            QShortcut(QKeySequence(seq), self, activated=slot)

        self.apply_settings(initial=True)
        self._update_buttons()
        QTimer.singleShot(100, self.new_game)

    # ------------------------------------------------------------ ajustes
    def apply_settings(self, initial=False):
        s = self.settings
        self.setStyleSheet(QSS.get(s.theme, QSS["oscuro"]))
        self.board.set_theme(s.theme)
        self.lbl_time.setVisible(s.show_timer)
        self.palette.show_counts = s.show_counts
        self.palette.update_counts(self.board.counts())
        self.audio.set_music(s.music_on, s.music_volume)
        self.audio.set_sfx(s.sfx_on, s.sfx_volume)
        self.btn_music.setText("Quitar música" if s.music_on else "Poner música")
        if not initial:
            if s.fullscreen and not self.isFullScreen():
                self.showFullScreen()
            elif not s.fullscreen and self.isFullScreen():
                self.showNormal()
        s.save()

    def showEvent(self, e):
        super().showEvent(e)
        if self.settings.fullscreen and not self.isFullScreen():
            QTimer.singleShot(0, self.showFullScreen)

    def toggle_fullscreen(self):
        self.settings.fullscreen = not self.isFullScreen()
        self.apply_settings()

    def toggle_music(self):
        self.settings.music_on = not self.settings.music_on
        self.apply_settings()

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.btn_assets.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(ASSETS_DIR))))
        dlg.btn_restore.clicked.connect(self._restore_images)
        if dlg.exec():
            dlg.apply_to(self.settings)
            self.apply_settings()

    def _restore_images(self):
        if QMessageBox.question(self, "Restaurar gráficos",
                                "Se sobrescribirán TODOS los gráficos de assets/img con los "
                                "originales. ¿Continuar?") == QMessageBox.StandardButton.Yes:
            ensure_default_images(IMG_DIR, overwrite=True)
            self.images.reload()
            self.palette.refresh_images()
            self.board.update()

    # ------------------------------------------------------------ generación
    def new_game(self):
        if self.gen is not None and self.gen.isRunning():
            return
        level = LEVELS[self.settings.level]
        self.gen = GeneratorThread(level)
        self.dialog = QProgressDialog("Generando puzzle...", "Cancelar", 0, 0, self)
        self.dialog.setWindowTitle(level.name)
        self.dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.dialog.setAutoClose(False)
        self.dialog.setAutoReset(False)
        self.dialog.setMinimumDuration(400)
        self.dialog.canceled.connect(self.gen.cancel)
        self.gen.progress.connect(self.dialog.setLabelText)
        self.gen.ready.connect(self._on_generated)
        self.gen.finished.connect(self._on_gen_finished)
        self.clock.stop()
        self.gen.start()

    def _on_generated(self, puzzle):
        self.load_puzzle(puzzle)

    def _on_gen_finished(self):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

    def load_puzzle(self, puzzle):
        self.puzzle = puzzle
        self.level = LEVELS[puzzle.level_key]
        self.board.setup(puzzle, self.level)
        self.palette.setup(self.level, self.settings.show_counts)
        self.palette.update_counts(self.board.counts())
        self.stats.started(self.level.key)
        self.seconds, self.hints, self.attempts = 0, 0, 0
        self.finished = False
        self.lbl_time.setText(fmt_time(0))
        self.lbl_level.setText(self.level.name)
        info = ("✔ Solución única garantizada" if puzzle.unique else
                "ℹ Puede haber varias soluciones: vale cualquiera que cumpla los números")
        if puzzle.fixed:
            info += f"\n{len(puzzle.fixed)} casilla(s) fija(s) como pista"
        self.lbl_info.setText(info)
        self.clock.start()
        self._update_buttons()

    # ------------------------------------------------------------ partida
    def _tick(self):
        self.seconds += 1
        self.lbl_time.setText(fmt_time(self.seconds))

    def _on_board_changed(self):
        self.palette.update_counts(self.board.counts())
        self._update_buttons()

    def _on_placed(self, code):
        name = SFX_BY_CATEGORY.get(category_of(code), "vacio")
        self.audio.play(name, fallback="place")

    def _update_buttons(self):
        playing = self.puzzle is not None and not self.finished
        for b in (self.btn_giveup, self.btn_check, self.btn_hint, self.btn_clear):
            b.setEnabled(playing)
        self.btn_undo.setEnabled(playing and bool(self.board.undo_stack))
        self.btn_redo.setEnabled(playing and bool(self.board.redo_stack))

    def _finish(self):
        self.finished = True
        self.clock.stop()
        self.board.readonly = True
        self._update_buttons()

    def check_play(self):
        if self.puzzle is None or self.finished:
            return
        n = self.puzzle.size
        mine = compute_numbers(self.board.grid, n)
        wrong = [i for i, (a, b) in enumerate(zip(mine, self.puzzle.numbers)) if a != b]
        good = [i for i in range(4 * n) if i not in wrong]
        if wrong:
            self.attempts += 1
            self.audio.play("lose")
            if self.settings.highlight_wrong:
                self.board.set_marks(wrong, good)
            QMessageBox.warning(
                self, "Incorrecto",
                f"Te has equivocado: {len(wrong)} de {4 * n} números no coinciden.")
            return
        cnt = self.board.counts()
        if (any(cnt.get(c, 0) != k for c, k in self.level.counts.items())
                or sum(cnt.values()) != n * n):
            self.board.set_marks([], good)
            QMessageBox.information(
                self, "Casi",
                "Todos los números coinciden, pero las piezas colocadas no son las "
                "indicadas para este nivel (revisa los contadores).")
            return
        self.board.set_marks([], good)
        self._finish()
        self.stats.won(self.level.key, self.seconds, self.hints == 0)
        self.audio.play("win")
        QMessageBox.information(
            self, "¡Correcto!",
            f"¡Enhorabuena! Resuelto en {fmt_time(self.seconds)}\n"
            f"Fallos al comprobar: {self.attempts} · Pistas usadas: {self.hints}")

    def give_up(self):
        if self.puzzle is None or self.finished:
            return
        if QMessageBox.question(self, "Me rindo", "¿Quieres ver la solución?"
                                ) != QMessageBox.StandardButton.Yes:
            return
        self.board.show_solution(self.puzzle.solution)
        self.palette.update_counts(self.board.counts())
        self.board.set_marks([], range(4 * self.puzzle.size))
        self._finish()
        self.stats.gave_up(self.level.key)

    def hint(self):
        if self.puzzle is None or self.finished:
            return
        if self.board.reveal_hint(self.puzzle.solution):
            self.hints += 1
        else:
            QMessageBox.information(self, "Pista", "No queda ninguna casilla por revelar.")

    def clear_board(self):
        if not self.finished:
            self.board.clear_all()

    def closeEvent(self, e):
        if self.gen is not None and self.gen.isRunning():
            self.gen.cancel()
            self.gen.wait(3000)
        self.settings.fullscreen = self.isFullScreen()
        self.settings.save()
        super().closeEvent(e)

"""Música de fondo (assets/music) y efectos de sonido (assets/sfx)."""
from PySide6.QtCore import QObject, QUrl

from .config import MUSIC_DIR, MUSIC_EXTS, SFX_DIR

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect
    HAVE_AUDIO = True
except ImportError:          # QtMultimedia no disponible
    HAVE_AUDIO = False


class AudioManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.music_on = False
        self.sfx_on = True
        self.tracks = []
        self.index = 0
        self.player = None
        self.effects = {}
        self.sfx_volume = 0.7
        if not HAVE_AUDIO:
            return
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.player.mediaStatusChanged.connect(self._on_status)
        self.reload()

    def reload(self):
        """Relee las carpetas de música y efectos."""
        self.tracks = sorted(p for p in MUSIC_DIR.glob("*")
                             if p.suffix.lower() in MUSIC_EXTS) if MUSIC_DIR.exists() else []
        self.effects.clear()
        if SFX_DIR.exists() and HAVE_AUDIO:
            for wav in SFX_DIR.glob("*.wav"):
                fx = QSoundEffect(self)
                fx.setSource(QUrl.fromLocalFile(str(wav)))
                fx.setVolume(self.sfx_volume)
                self.effects[wav.stem] = fx

    # ----- música
    def set_music(self, on: bool, volume_percent: int):
        if not HAVE_AUDIO:
            return
        self.output.setVolume(max(0, min(100, volume_percent)) / 100.0)
        if on and not self.music_on:
            self.music_on = True
            self._play_current()
        elif not on and self.music_on:
            self.music_on = False
            self.player.pause()

    def _play_current(self):
        if not self.tracks:
            return
        self.index %= len(self.tracks)
        if self.player.source() != QUrl.fromLocalFile(str(self.tracks[self.index])):
            self.player.setSource(QUrl.fromLocalFile(str(self.tracks[self.index])))
        self.player.play()

    def next_track(self):
        if self.tracks:
            self.index = (self.index + 1) % len(self.tracks)
            if self.music_on:
                self.player.setSource(QUrl.fromLocalFile(str(self.tracks[self.index])))
                self.player.play()

    def _on_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.music_on:
            if len(self.tracks) == 1:       # bucle de una sola pista
                self.player.setPosition(0)
                self.player.play()
            else:
                self.next_track()

    # ----- efectos
    def set_sfx(self, on: bool, volume_percent: int):
        self.sfx_on = on
        self.sfx_volume = max(0, min(100, volume_percent)) / 100.0
        for fx in self.effects.values():
            fx.setVolume(self.sfx_volume)

    def play(self, name: str, fallback: str = None):
        """Reproduce assets/sfx/<name>.wav; si no existe, prueba con `fallback`."""
        fx = self.effects.get(name) or (self.effects.get(fallback) if fallback else None)
        if self.sfx_on and fx is not None:
            fx.stop()
            fx.play()

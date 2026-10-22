"""La casa encantada - punto de entrada."""
import sys

from PySide6.QtWidgets import QApplication

from casa_encantada.assets_gen import ensure_default_images, ensure_default_sfx
from casa_encantada.audio import AudioManager
from casa_encantada.config import IMG_DIR, MUSIC_DIR, SFX_DIR, Settings, Stats
from casa_encantada.ui.images import ImageStore
from casa_encantada.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("La casa encantada")
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    ensure_default_images(IMG_DIR)
    ensure_default_sfx(SFX_DIR)
    settings, stats = Settings.load(), Stats()
    audio = AudioManager()
    window = MainWindow(settings, stats, audio, ImageStore())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

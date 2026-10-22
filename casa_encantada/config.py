"""Rutas, configuración del usuario y estadísticas (JSON)."""
import json
from dataclasses import dataclass, asdict, fields
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent
ASSETS_DIR = ROOT_DIR / "assets"
IMG_DIR = ASSETS_DIR / "img"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"
USER_DIR = Path.home() / ".casa_encantada"

MUSIC_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


@dataclass
class Settings:
    fullscreen: bool = False
    level: str = "facil"
    music_on: bool = True
    music_volume: int = 50
    sfx_on: bool = True
    sfx_volume: int = 70
    theme: str = "oscuro"          # "oscuro" | "claro"
    highlight_wrong: bool = True   # resaltar números erróneos al comprobar
    show_timer: bool = True
    show_counts: bool = True       # contadores de piezas en la paleta

    @classmethod
    def load(cls):
        s = cls()
        try:
            data = json.loads((USER_DIR / "settings.json").read_text(encoding="utf-8"))
            for f in fields(cls):
                if f.name in data:
                    setattr(s, f.name, type(getattr(s, f.name))(data[f.name]))
        except (OSError, ValueError, TypeError):
            pass
        return s

    def save(self):
        try:
            USER_DIR.mkdir(parents=True, exist_ok=True)
            (USER_DIR / "settings.json").write_text(
                json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass


class Stats:
    """Estadísticas por nivel: jugadas, ganadas, rendidas, mejor tiempo."""

    def __init__(self):
        self.data = {}
        try:
            self.data = json.loads((USER_DIR / "stats.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}

    def level(self, key):
        return self.data.setdefault(
            key, {"played": 0, "won": 0, "gave_up": 0, "best": None, "total_time": 0})

    def started(self, key):
        self.level(key)["played"] += 1
        self.save()

    def won(self, key, seconds, clean):
        d = self.level(key)
        d["won"] += 1
        d["total_time"] += seconds
        if clean and (d["best"] is None or seconds < d["best"]):
            d["best"] = seconds
        self.save()

    def gave_up(self, key):
        self.level(key)["gave_up"] += 1
        self.save()

    def reset(self):
        self.data = {}
        self.save()

    def save(self):
        try:
            USER_DIR.mkdir(parents=True, exist_ok=True)
            (USER_DIR / "stats.json").write_text(
                json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600}h {seconds % 3600 // 60}m {seconds % 60}s"

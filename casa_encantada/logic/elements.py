"""Definición de los elementos que puede contener una celda y de los niveles.

Códigos de celda (enteros):
    0  EMPTY      celda sin rellenar (transparente, no cuenta nada)
    1  ZOMBIE     se ve siempre
    2  VAMPIRE    se ve solo ANTES de reflejarse
    3  GHOST      se ve solo DESPUÉS de reflejarse al menos una vez
    4  BLOCK      opaco: el rayo muere aquí
    5  MIRROR2_SLASH       espejo doble cara '/'
    6  MIRROR2_BACKSLASH   espejo doble cara '\\'
    10..17 espejo de UNA cara:  10 + diag*4 + face*2 + back
        diag: 0 = '/', 1 = '\\'
        face: cuál de las dos caras refleja
              '/'  -> 0 = cara NO (arriba-izq),  1 = cara SE (abajo-der)
              '\\' -> 0 = cara SO (abajo-izq),   1 = cara NE (arriba-der)
        back: 0 = la otra cara es BLANCA (el rayo la atraviesa)
              1 = la otra cara es NEGRA  (el rayo se detiene)
"""
from dataclasses import dataclass

EMPTY, ZOMBIE, VAMPIRE, GHOST, BLOCK = 0, 1, 2, 3, 4
MIRROR2_SLASH, MIRROR2_BACKSLASH = 5, 6
MIRROR1_FIRST, MIRROR1_LAST = 10, 17

# Categorías (para contar piezas y para la paleta)
CAT_ZOMBIE, CAT_VAMPIRE, CAT_GHOST = "zombi", "vampiro", "fantasma"
CAT_MIRROR2, CAT_MIRROR1, CAT_BLOCK = "espejo2", "espejo1", "bloque"

CATEGORY_CODES = {
    CAT_ZOMBIE: [ZOMBIE],
    CAT_VAMPIRE: [VAMPIRE],
    CAT_GHOST: [GHOST],
    CAT_MIRROR2: [MIRROR2_SLASH, MIRROR2_BACKSLASH],
    CAT_MIRROR1: list(range(MIRROR1_FIRST, MIRROR1_LAST + 1)),
    CAT_BLOCK: [BLOCK],
}
CATEGORY_NAMES = {
    CAT_ZOMBIE: "Zombis",
    CAT_VAMPIRE: "Vampiros",
    CAT_GHOST: "Fantasmas",
    CAT_MIRROR2: "Espejos doble cara",
    CAT_MIRROR1: "Espejos 1 cara",
    CAT_BLOCK: "Bloques",
}


def category_of(code: int):
    if code == EMPTY:
        return None
    for cat, codes in CATEGORY_CODES.items():
        if code in codes:
            return cat
    return None


def mirror1_parts(code: int):
    """Devuelve (diag, face, back) de un espejo de una cara."""
    v = code - MIRROR1_FIRST
    return v // 4, (v // 2) % 2, v % 2


def element_key(code: int) -> str:
    """Nombre de archivo (sin extensión) del gráfico de un elemento."""
    names = {EMPTY: "vacio", ZOMBIE: "zombi", VAMPIRE: "vampiro",
             GHOST: "fantasma", BLOCK: "bloque",
             MIRROR2_SLASH: "espejo2_barra", MIRROR2_BACKSLASH: "espejo2_contrabarra"}
    if code in names:
        return names[code]
    d, f, b = mirror1_parts(code)
    return f"espejo1_{'barra' if d == 0 else 'contrabarra'}_cara{f}_{'blanco' if b == 0 else 'negro'}"


ALL_CODES = [EMPTY, ZOMBIE, VAMPIRE, GHOST, BLOCK, MIRROR2_SLASH, MIRROR2_BACKSLASH] + \
            list(range(MIRROR1_FIRST, MIRROR1_LAST + 1))


@dataclass(frozen=True)
class Level:
    key: str
    name: str
    size: int
    counts: dict          # categoría -> cantidad (suman size*size)
    time_budget: float    # segundos máximos buscando solución única
    max_clues: int        # pistas fijas máximas si no se logra unicidad

    @property
    def categories(self):
        return [c for c, n in self.counts.items() if n > 0]


LEVELS = {
    "facil": Level("facil", "Fácil (3x3)", 3,
                   {CAT_MIRROR2: 3, CAT_ZOMBIE: 3, CAT_VAMPIRE: 3}, 4.0, 3),
    "normal": Level("normal", "Normal (4x4)", 4,
                    {CAT_MIRROR2: 4, CAT_ZOMBIE: 4, CAT_VAMPIRE: 4, CAT_GHOST: 4}, 8.0, 5),
    "dificil": Level("dificil", "Difícil (5x5)", 5,
                     {CAT_MIRROR2: 4, CAT_ZOMBIE: 4, CAT_VAMPIRE: 4, CAT_GHOST: 4,
                      CAT_MIRROR1: 5, CAT_BLOCK: 4}, 8.0, 8),
}
LEVEL_ORDER = ["facil", "normal", "dificil"]


_FACE_NAMES = {(0, 0): "arriba-izquierda", (0, 1): "abajo-derecha",
               (1, 0): "abajo-izquierda", (1, 1): "arriba-derecha"}


def describe(code: int) -> str:
    """Texto descriptivo (para tooltips) de un elemento."""
    simple = {EMPTY: "Casilla vacía (no cuenta ni bloquea)",
              ZOMBIE: "Zombi: se ve siempre, directo o reflejado",
              VAMPIRE: "Vampiro: solo se ve en directo, nunca reflejado",
              GHOST: "Fantasma: solo se ve a través de un espejo",
              BLOCK: "Bloque: opaco, el rayo se detiene",
              MIRROR2_SLASH: "Espejo doble cara  /",
              MIRROR2_BACKSLASH: "Espejo doble cara  \\"}
    if code in simple:
        return simple[code]
    d, f, b = mirror1_parts(code)
    back = ("dorso blanco: el rayo lo atraviesa" if b == 0
            else "dorso negro: el rayo se detiene")
    return (f"Espejo de una cara {'/' if d == 0 else chr(92)} · refleja por la cara "
            f"{_FACE_NAMES[(d, f)]} · {back}")

"""Generador de puzzles con intento de solución única."""
import random
import time
from dataclasses import dataclass, field

from .elements import CATEGORY_CODES, Level
from .raytrace import compute_numbers, ray_starts, ACTIONS, DR, DC, STOP, REFLECT
from .solver import solve


@dataclass
class Puzzle:
    level_key: str
    size: int
    counts: dict
    numbers: list              # 4n números del borde
    solution: list             # cuadrícula n x n de códigos
    fixed: dict = field(default_factory=dict)   # {(fila, col): código} pistas
    unique: bool = False       # solución única demostrada

    def to_dict(self):
        return {"level": self.level_key, "size": self.size, "counts": self.counts,
                "numbers": self.numbers, "solution": self.solution,
                "fixed": [[r, c, v] for (r, c), v in self.fixed.items()],
                "unique": self.unique}

    @staticmethod
    def from_dict(d):
        return Puzzle(d["level"], d["size"], d["counts"], d["numbers"], d["solution"],
                      {(r, c): v for r, c, v in d["fixed"]}, d["unique"])


def random_layout(level: Level, rng: random.Random):
    pieces = []
    for cat, k in level.counts.items():
        for _ in range(k):
            pieces.append(rng.choice(CATEGORY_CODES[cat]))
    rng.shuffle(pieces)
    n = level.size
    return [pieces[r * n:(r + 1) * n] for r in range(n)]


def hidden_cells(grid, n):
    """Celdas que ningún rayo atraviesa (su contenido sería indeterminable)."""
    seen = set()
    for (r, c, d) in ray_starts(n):
        reflected_seen = 0
        while 0 <= r < n and 0 <= c < n:
            bit = 1 << ((r * n + c) * 4 + d)
            if reflected_seen & bit:
                break
            reflected_seen |= bit
            seen.add((r, c))
            kind, nd = ACTIONS[grid[r][c]][d]
            if kind == STOP:
                break
            if kind == REFLECT:
                d = nd
            r += DR[d]
            c += DC[d]
    return [(r, c) for r in range(n) for c in range(n) if (r, c) not in seen]


def _candidate(level, rng, max_hidden, tries=400):
    """Layout aleatorio con como mucho `max_hidden` celdas ocultas."""
    n = level.size
    best = None
    for _ in range(tries):
        grid = random_layout(level, rng)
        hid = hidden_cells(grid, n)
        if len(hid) <= max_hidden:
            return grid, hid
        if best is None or len(hid) < len(best[1]):
            best = (grid, hid)
    return best


def _refine(level, grid, numbers, rng, cancel, per_solve, deadline, fixed):
    """Añade pistas fijas hasta lograr solución única.

    Devuelve el dict de pistas, o None si el candidato es demasiado costoso.
    """
    n = level.size
    fixed = dict(fixed)
    while True:
        if cancel and cancel():
            raise InterruptedError
        if len(fixed) > level.max_clues:
            return None
        left = max(0.2, min(per_solve, deadline - time.monotonic()))
        sols, complete = solve(n, numbers, level.counts, fixed, limit=2,
                               max_seconds=left, cancel=cancel)
        if complete and len(sols) == 1:
            return fixed
        if len(fixed) >= level.max_clues:
            return None
        free = [(r, c) for r in range(n) for c in range(n) if (r, c) not in fixed]
        if complete and len(sols) == 2:
            diff = [(r, c) for (r, c) in free if sols[0][r][c] != sols[1][r][c]]
            pool = diff or free
        else:                      # solver abortado: pista aleatoria
            pool = free
        r, c = rng.choice(pool)
        fixed[(r, c)] = grid[r][c]


def generate(level: Level, rng=None, progress=None, cancel=None, time_budget=None):
    """Crea un puzzle. `progress(texto)` y `cancel()` son opcionales.

    Fase 1: layouts sin celdas ocultas, sin pistas, hasta demostrar unicidad.
    Fase 2: layouts con pistas fijas mínimas (celdas ocultas + las que
            diferencien dos soluciones) hasta demostrar unicidad.
    Fase 3: si se agota el tiempo, devuelve el mejor candidato con varias
            soluciones posibles (al comprobar se acepta cualquiera que
            cumpla todos los números).
    """
    rng = rng or random.Random()
    n = level.size
    budget = time_budget if time_budget is not None else level.time_budget
    t0 = time.monotonic()
    phase1_end = t0 + budget * 0.4
    deadline = t0 + budget
    attempts = 0
    fallback = None            # (celdas_ocultas, grid, numbers)

    def mk(grid, numbers, fixed, unique):
        return Puzzle(level.key, n, dict(level.counts), numbers, grid, fixed, unique)

    while time.monotonic() < phase1_end:
        if cancel and cancel():
            raise InterruptedError
        attempts += 1
        if progress:
            progress(f"Buscando solución única... intento {attempts}")
        grid, hid = _candidate(level, rng, 0)
        numbers = compute_numbers(grid, n)
        if fallback is None or len(hid) < len(fallback[0]):
            fallback = (hid, grid, numbers)
        if hid:
            continue
        sols, complete = solve(n, numbers, level.counts, limit=2,
                               max_seconds=min(1.0, budget), cancel=cancel)
        if complete and len(sols) == 1:
            return mk(grid, numbers, {}, True)
    best = None
    while time.monotonic() < deadline:
        if cancel and cancel():
            raise InterruptedError
        attempts += 1
        if progress:
            progress(f"Ajustando pistas... intento {attempts}")
        grid, hid = _candidate(level, rng, max(1, level.max_clues // 2))
        numbers = compute_numbers(grid, n)
        if fallback is None or len(hid) < len(fallback[0]):
            fallback = (hid, grid, numbers)
        fixed0 = {(r, c): grid[r][c] for (r, c) in hid}
        fixed = _refine(level, grid, numbers, rng, cancel, 1.2, deadline, fixed0)
        if fixed is not None:
            if best is None or len(fixed) < len(best.fixed):
                best = mk(grid, numbers, fixed, True)
            if len(fixed) <= max(1, level.max_clues // 3):
                break
    if best:
        return best
    hid, grid, numbers = fallback
    fixed = {(r, c): grid[r][c] for (r, c) in hid[:level.max_clues]}
    return mk(grid, numbers, fixed, False)

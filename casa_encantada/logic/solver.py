"""Resolutor por backtracking con poda por rayos parciales.

Orden dinámico: en cada nodo se traza cada uno de los 4n rayos hasta la
primera celda sin asignar (su "frontera"). Si un rayo terminó, su cuenta
debe igualar el número del borde; si no, su cuenta parcial (cota inferior
exacta) no puede superarlo. La siguiente celda a rellenar es la frontera de
más rayos, de modo que cada asignación extiende varios rayos a la vez.
"""
import time
from .elements import CATEGORY_CODES, category_of
from .raytrace import ray_starts, ACTIONS, DR, DC, PASS, STOP
from .elements import ZOMBIE, VAMPIRE, GHOST

UNSET = -1


class SolveAbort(Exception):
    pass


def _trace_frontier(grid, n, r, c, d):
    """(cuenta, terminado, fila_frontera, col_frontera)."""
    count = 0
    reflected = False
    seen = 0
    while 0 <= r < n and 0 <= c < n:
        code = grid[r][c]
        if code == UNSET:
            return count, False, r, c
        bit = 1 << ((r * n + c) * 4 + d)
        if seen & bit:          # bucle: se detiene (misma regla que raytrace.trace)
            return count, True, -1, -1
        seen |= bit
        if code == ZOMBIE:
            count += 1
        elif code == VAMPIRE:
            if not reflected:
                count += 1
        elif code == GHOST:
            if reflected:
                count += 1
        else:
            kind, nd = ACTIONS[code][d]
            if kind == STOP:
                return count, True, -1, -1
            if kind != PASS:
                d = nd
                reflected = True
        r += DR[d]
        c += DC[d]
    return count, True, -1, -1


def solve(n, targets, counts, fixed=None, limit=2, max_seconds=None,
          max_nodes=None, cancel=None):
    """Busca soluciones.

    counts: {categoría: cantidad} de piezas a colocar (incluidas las fijas).
    fixed:  {(fila, col): código} piezas ya colocadas (pistas).
    Devuelve (lista_de_soluciones, completo). `completo` es True si se
    exploró todo el espacio (o se alcanzó `limit`) sin agotar el presupuesto.
    """
    fixed = fixed or {}
    grid = [[UNSET] * n for _ in range(n)]
    remaining = dict(counts)
    for (r, c), code in fixed.items():
        grid[r][c] = code
        remaining[category_of(code)] -= 1
    if any(v < 0 for v in remaining.values()):
        return [], True
    free = n * n - len(fixed)
    if sum(remaining.values()) != free:
        raise ValueError("Las cantidades no suman las celdas libres")
    cats = list(remaining)
    starts = ray_starts(n)
    solutions = []
    nodes = [0]
    deadline = time.monotonic() + max_seconds if max_seconds else None

    def rec(unassigned):
        nodes[0] += 1
        if max_nodes and nodes[0] > max_nodes:
            raise SolveAbort
        if (nodes[0] & 127) == 0:
            if deadline and time.monotonic() > deadline:
                raise SolveAbort
            if cancel is not None and cancel():
                raise SolveAbort
        votes = {}
        for (r, c, d), t in zip(starts, targets):
            cnt, done, fr, fc = _trace_frontier(grid, n, r, c, d)
            if cnt > t or (done and cnt != t):
                return False
            if not done:
                votes[(fr, fc)] = votes.get((fr, fc), 0) + 1
        if unassigned == 0:
            solutions.append([row[:] for row in grid])
            return len(solutions) >= limit
        if votes:
            cell = max(votes, key=votes.get)
        else:  # celdas que ningún rayo alcanza: cualquier asignación vale
            cell = next((r, c) for r in range(n) for c in range(n) if grid[r][c] == UNSET)
        r, c = cell
        for cat in cats:
            if remaining[cat] <= 0:
                continue
            remaining[cat] -= 1
            for code in CATEGORY_CODES[cat]:
                grid[r][c] = code
                if rec(unassigned - 1):
                    grid[r][c] = UNSET
                    remaining[cat] += 1
                    return True
            grid[r][c] = UNSET
            remaining[cat] += 1
        return False

    try:
        rec(free)
        return solutions, True
    except SolveAbort:
        return solutions, len(solutions) >= limit

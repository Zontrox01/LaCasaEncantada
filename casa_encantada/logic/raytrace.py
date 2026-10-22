"""Trazado de rayos sobre la cuadrícula.

Direcciones: 0 = arriba (N), 1 = derecha (E), 2 = abajo (S), 3 = izquierda (O).
Las etiquetas del borde se ordenan: ARRIBA (izq->der), ABAJO (izq->der),
IZQUIERDA (arriba->abajo), DERECHA (arriba->abajo).
"""
from .elements import (EMPTY, ZOMBIE, VAMPIRE, GHOST, BLOCK, MIRROR2_SLASH,
                       MIRROR2_BACKSLASH, MIRROR1_FIRST, MIRROR1_LAST, mirror1_parts)

N, E, S, W = 0, 1, 2, 3
DR = (-1, 0, 1, 0)
DC = (0, 1, 0, -1)

PASS, REFLECT, STOP = 0, 1, 2

# Reflexión por tipo de diagonal
_SLASH = {E: N, N: E, W: S, S: W}
_BACK = {E: S, S: E, W: N, N: W}
# Caras: dirección de viaje con la que se golpea cada cara
_FACE_DIRS = {
    (0, 0): (E, S),   # '/'  cara arriba-izquierda
    (0, 1): (W, N),   # '/'  cara abajo-derecha
    (1, 0): (E, N),   # '\' cara abajo-izquierda
    (1, 1): (W, S),   # '\' cara arriba-derecha
}


def _build_actions():
    act = {}
    for code in (EMPTY, ZOMBIE, VAMPIRE, GHOST):
        act[code] = [(PASS, 0)] * 4
    act[BLOCK] = [(STOP, 0)] * 4
    act[MIRROR2_SLASH] = [(REFLECT, _SLASH[d]) for d in range(4)]
    act[MIRROR2_BACKSLASH] = [(REFLECT, _BACK[d]) for d in range(4)]
    for code in range(MIRROR1_FIRST, MIRROR1_LAST + 1):
        diag, face, back = mirror1_parts(code)
        table = _SLASH if diag == 0 else _BACK
        row = []
        for d in range(4):
            if d in _FACE_DIRS[(diag, face)]:
                row.append((REFLECT, table[d]))
            else:
                row.append((STOP, 0) if back == 1 else (PASS, 0))
        act[code] = row
    return act


ACTIONS = _build_actions()


def ray_starts(n):
    """Lista de (fila, col, dirección) de los 4n rayos en el orden de las etiquetas."""
    starts = []
    for c in range(n):
        starts.append((0, c, S))
    for c in range(n):
        starts.append((n - 1, c, N))
    for r in range(n):
        starts.append((r, 0, E))
    for r in range(n):
        starts.append((r, n - 1, W))
    return starts


def trace(grid, n, r, c, d, unknown=None):
    """Sigue un rayo. Devuelve (cuenta, completo).

    `completo` es False si el rayo llega a una celda aún no asignada
    (valor `unknown`); en ese caso `cuenta` es una cota inferior exacta
    de lo visto hasta ahora.

    Regla de bucles: con espejos de una cara un rayo puede entrar en un
    circuito cerrado. Se detiene al volver a una celda con la misma
    dirección con la que ya la atravesó (sin contar de nuevo).
    """
    count = 0
    reflected = False
    seen = 0
    while 0 <= r < n and 0 <= c < n:
        code = grid[r][c]
        if unknown is not None and code == unknown:
            return count, False
        bit = 1 << ((r * n + c) * 4 + d)
        if seen & bit:
            return count, True
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
                return count, True
            if kind == REFLECT:
                d = nd
                reflected = True
        r += DR[d]
        c += DC[d]
    return count, True


def compute_numbers(grid, n):
    """Los 4n números del borde para una cuadrícula completa."""
    return [trace(grid, n, r, c, d)[0] for (r, c, d) in ray_starts(n)]

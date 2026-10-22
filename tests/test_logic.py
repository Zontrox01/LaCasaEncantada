import os, random, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from casa_encantada.logic.elements import *
from casa_encantada.logic.raytrace import compute_numbers, trace
from casa_encantada.logic.solver import solve
from casa_encantada.logic.generator import generate


def test_basic_rays():
    # fila con zombi, vampiro, fantasma
    g = [[ZOMBIE, VAMPIRE, GHOST], [BLOCK, BLOCK, BLOCK], [BLOCK, BLOCK, BLOCK]]
    nums = compute_numbers(g, 3)
    # arriba: col0 ve zombi(1) y luego bloque ->1 ; col1 vampiro 1; col2 fantasma 0
    assert nums[0:3] == [1, 1, 0]
    # izquierda fila0: zombi + vampiro = 2 ; derecha fila0: fantasma 0 + vampiro 1 + zombi 1 = 2
    assert nums[6] == 2 and nums[9] == 2
    # fantasma solo tras reflejo: espejo '/' en (0,0), rayo desde la izq. va E -> N, sale
    g2 = [[MIRROR2_SLASH, GHOST, VAMPIRE], [BLOCK] * 3, [BLOCK] * 3]
    assert trace(g2, 3, 0, 0, 1)[0] == 0
    # rayo desde arriba col0 (dir S) en '/': S->W sale
    assert trace(g2, 3, 0, 0, 2)[0] == 0
    # '/' en (1,0) desde izquierda: E->N sube a (0,0)...
    g3 = [[ZOMBIE, ZOMBIE, ZOMBIE], [MIRROR2_SLASH, BLOCK, BLOCK], [BLOCK] * 3]
    assert trace(g3, 3, 1, 0, 1)[0] == 1      # sube, cuenta zombi (0,0)
    g4 = [[GHOST, VAMPIRE, ZOMBIE], [MIRROR2_SLASH, BLOCK, BLOCK], [BLOCK] * 3]
    assert trace(g4, 3, 1, 0, 1)[0] == 1      # fantasma visto tras reflejo
    g5 = [[VAMPIRE, 0, 0], [MIRROR2_SLASH, BLOCK, BLOCK], [BLOCK] * 3]
    assert trace(g5, 3, 1, 0, 1)[0] == 0      # vampiro no se ve reflejado


def test_single_sided():
    # '/' cara0 (NO) refleja, dorso blanco: viajando E refleja a N; viajando W atraviesa
    code = 10 + 0 * 4 + 0 * 2 + 0
    g = [[ZOMBIE, ZOMBIE, ZOMBIE], [ZOMBIE, code, ZOMBIE], [ZOMBIE] * 3]
    assert trace(g, 3, 1, 0, 1)[0] == 1 + 1      # zombi(1,0) + sube: zombi (0,1)... 
    assert trace(g, 3, 1, 2, 3)[0] == 2  # atraviesa: zombi(1,2) + zombi(1,0)
    black = 10 + 0 * 4 + 0 * 2 + 1
    g[1][1] = black
    assert trace(g, 3, 1, 2, 3)[0] == 1          # se detiene en el dorso negro


def test_no_infinite_loops_and_consistency():
    """Los dos trazadores coinciden y siempre terminan, incluso con bucles."""
    from casa_encantada.logic.generator import random_layout
    from casa_encantada.logic.solver import _trace_frontier
    from casa_encantada.logic.raytrace import ray_starts
    rng = random.Random(1)
    lvl = LEVELS["dificil"]
    for _ in range(3000):
        g = random_layout(lvl, rng)
        for (r, c, d) in ray_starts(5):
            a = trace(g, 5, r, c, d)
            b = _trace_frontier(g, 5, r, c, d)
            assert a[0] == b[0] and b[1] is True


def test_levels_unique():
    for key in LEVEL_ORDER:
        lvl = LEVELS[key]
        t = time.time()
        p = generate(lvl, random.Random(7))
        nums_ok = compute_numbers(p.solution, p.size) == p.numbers
        print(key, "unique=%s clues=%d time=%.1fs" % (p.unique, len(p.fixed), time.time() - t))
        assert nums_ok
        sols, comp = solve(p.size, p.numbers, p.counts, p.fixed, limit=2, max_seconds=20)
        assert len(sols) >= 1
        if p.unique:
            assert comp and len(sols) == 1


if __name__ == "__main__":
    test_basic_rays(); test_single_sided(); test_no_infinite_loops_and_consistency(); test_levels_unique(); print("OK")

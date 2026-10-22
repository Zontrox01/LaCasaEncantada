# La casa encantada

Juego de lógica en Python + PySide6. Coloca zombis, vampiros, fantasmas, espejos y
bloques para que todos los números del borde coincidan.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/UI-PySide6%20(Qt6)-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## Ejecutar
```
pip install -r requirements.txt
python main.py
```
Probado con Python 3.10 / PySide6 6.x. La primera vez se generan los gráficos y sonidos
por defecto en `assets/`.

## Reglas
- Cada casilla lleva UNA pieza. Los números del borde = monstruos que se ven mirando
  desde ese lado (los monstruos no bloquean; se cuentan una vez por cada paso).
- Zombi: siempre · Vampiro: solo antes de reflejarse · Fantasma: solo después de reflejarse.
- Espejo doble cara `/` `\` · Espejo de una cara (cara plateada refleja; el dorso es blanco =
  transparente, o negro = detiene el rayo) · Bloque: opaco.
- Si con espejos de una cara el rayo entra en un circuito cerrado, se detiene al repetir
  casilla y dirección.

| Nivel | Tamaño | Piezas |
|---|---|---|
| Fácil | 3x3 | 3 espejos doble cara, 3 zombis, 3 vampiros |
| Normal | 4x4 | 4 espejos doble cara, 4 zombis, 4 vampiros, 4 fantasmas |
| Difícil | 5x5 | lo anterior + 5 espejos de una cara + 4 bloques |

Fácil y Normal: solución única demostrada por un resolutor propio. Difícil: se intenta,
pero normalmente hay varias soluciones; al comprobar vale cualquiera que cumpla los números.

## Controles
Clic = siguiente pieza · Mayús+clic/rueda = anterior · Clic derecho = girar espejo ·
Arrastrar desde la paleta · Arrastrar una pieza fuera del tablero = quitarla ·
Ctrl+Z / Ctrl+Y · F11 pantalla completa · Ctrl+N nueva partida.

## Personalizar
- `assets/img/*.png`: gráficos (160x160, mismo nombre). Si borras uno se regenera.
- `assets/music/`: pon tus .mp3/.ogg/.wav/.flac; suenan en bucle.
- `assets/sfx/`: click, place, win, lose (.wav).
- Configuración y estadísticas: `~/.casa_encantada/`.

## Estructura
```
main.py
casa_encantada/
  config.py  assets_gen.py  audio.py
  logic/   elements.py  raytrace.py  solver.py  generator.py
  ui/      main_window.py  board.py  palette.py  dialogs.py  images.py
tests/test_logic.py
```

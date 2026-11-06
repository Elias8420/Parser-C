# Parser de C++

Analizador sintáctico para un subconjunto de C++, escrito en Python con la técnica de **descenso recursivo**. Recibe código fuente como texto, verifica que cumpla la gramática definida y, si es válido, construye un **árbol de análisis sintáctico**. Si no lo es, se detiene con un mensaje que indica la línea, la columna y qué se esperaba.

## Flujo general

```
texto  ──►  lexer.py  ──►  lista de tokens  ──►  parser.py  ──►  árbol (tree.py)
                                                      │
                                                      └──►  error (línea, columna, qué se esperaba)
```

| Módulo | Responsabilidad | Entrada | Salida |
|---|---|---|---|
| `lexer.py` | Corta el texto en tokens
| `parser.py` | Verificar que los tokens sigan la gramática y armar el árbol
| `tree.py` | Definir cómo se guarda e imprime el árbol

## `lexer.py`: del texto a los tokens

El lexer recorre el texto de izquierda a derecha y lo corta en **tokens**. Descarta los espacios y los comentarios, y lleva la cuenta de la línea y la columna de cada pieza.

### El token

```python
@dataclass
class Token:
    tipo: str    # categoría: 'ID', 'NUM', 'INCLUDE', 'EOF', etc.
    valor: str   # texto exacto que se leyó
    linea: int   # línea donde apareció
    col: int     # columna donde empezó
```
### Qué reconoce

| Categoría | Patrón (regex) | Ejemplos |
|---|---|---|
| `COMENTARIO` | `//[^\n]*` | `// nota` (se descarta) |
| `INCLUDE` | `\#include[ \t]*<[A-Za-z_][\w./]*>` | `#include <iostream>` |
| `NUEVA_LINEA` | `\n` | (solo cuenta líneas) |
| `ESPACIO` | `[ \t\r]+` | (se descarta) |
| `NUM` | `\d+(\.\d+)?` | `5`, `3.14` |
| `ID` | `[A-Za-z_]\w*` | `x`, `contador1`, `_tmp` |
| `OP2` | `==`, `!=`, `<=`, `>=`, `&&`, `\|\|`, `<<`, `++`, `--`, `+=`, `-=` | operadores de dos caracteres |
| `OP1` | `+ - * / < > = ! ( ) { } ; : ,` | operadores y signos de un carácter |
| `ERROR` | `.` | cualquier otro carácter |

**Palabras reservadas:** `int`, `float`, `bool`, `void`, `if`, `else`, `while`, `do`, `for`, `switch`, `case`, `default`, `break`, `continue`, `return`, `cout`, `true`, `false`, `using`, `namespace`.

## `tree.py`: el árbol de análisis

Define la clase `Nodo`, que es la estructura donde el parser va guardando lo que reconoce.

```pyth
## `tree.py`: el árbol de análisis

Define la clase `Nodo`, que es la estructura donde el parser va guardando lo que reconoce.
```
| Atributo | Descripción |
|---|---|
| `etiqueta` | Nombre del nodo: `'while'`, `'suma'`, `'ID'`, `'('` ... |
| `hijos` | Lista de nodos hijos. Las hojas tienen la lista vacía |
| `valor` | Texto concreto de la hoja (`'x'`, `'5'`). En el resto es `None` |
| `imprimir()` | Dibuja el árbol en consola con `├──` y `└──` |
| `a_nltk()` | Convierte el árbol a `nltk.Tree` (requiere tener `nltk` instalado) |
```pyth
El árbol es un **árbol de análisis** (parse tree): conserva los símbolos de la gramática, incluidos `;`, `(` y `{`. No es un AST, que los descartaría.

### Ejemplo de salida

Para `int main() { x = 1 + 2 * 3; }`:

```pyth
programa
└── funcion
    ├── tipo
    │   └── int
    ├── ID: main
    ├── (
    ├── params
    ├── )
    └── bloque
        ├── {
        ├── asignacion
        │   ├── ID: x
        │   ├── =
        │   ├── suma
        │   │   ├── NUM: 1
        │   │   ├── +
        │   │   └── term
        │   │       ├── NUM: 2
        │   │       ├── *
        │   │       └── NUM: 3
        │   └── ;
        └── }
```

La multiplicación queda más adentro que la suma: así se refleja la precedencia de operadores.

---

## `parser.py`: la gramática

El parser recibe la lista de tokens y verifica que sigan la gramática. Es un **parser descendente recursivo**: cada regla de la gramática es un método de la clase `Parser`, y cuando una regla menciona otra, el método llama al otro.

### Limitaciones del subconjunto

- No hay cadenas de texto, arreglos, punteros, clases ni declaraciones globales.
- `cout` acepta una sola expresión (no `cout << x << endl;`).
- `case` solo acepta números, no expresiones.
- Una comparación no se puede encadenar (`a < b < c` se rechaza), y `==` y `<` comparten nivel de precedencia.
- En el `for`, la inicialización y el paso solo pueden ser declaraciones o asignaciones.

---
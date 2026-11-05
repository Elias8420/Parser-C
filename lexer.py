import re
from dataclasses import dataclass

PALABRAS_RESERVADAS = {
    "int", "float", "bool", "void", "if", "else", "while", "do", "for",
    "switch", "case", "default", "break", "continue", "return",
    "cout", "true", "false", "using", "namespace"
}


class ErrorLexico(Exception):
    pass


@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    col: int

ESPECIFICACION = [
    ("COMENTARIO", r"//[^\n]*"),
    ("INCLUDE", r"\#include[ \t]*<[A-Za-z_][\w./]*>"),
    ("NUEVA_LINEA", r"\n"),
    ("ESPACIO", r"[ \t\r]+"),
    ("NUM", r"\d+(\.\d+)?"),
    ("ID", r"[A-Za-z_]\w*"),
    ("OP2", r"==|!=|<=|>=|&&|\|\||<<|\+\+|--|\+=|-="),
    ("OP1", r"[+\-*/<>=!(){};:,]"),
    ("ERROR", r"."),
]
PATRON = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPECIFICACION))
import re
from dataclasses import dataclass

PALABRAS_RESERVADAS = {
    "int", "float", "bool", "void", "if", "else", "while", "do", "for",
    "switch", "case", "default", "break", "continue", "return",
    "cout", "true", "false", "using", "namespace"
}


class ErrorLexico(Exception):
    pass


@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    col: int

ESPECIFICACION = [
    ("COMENTARIO", r"//[^\n]*"),
    ("INCLUDE", r"\#include[ \t]*<[A-Za-z_][\w./]*>"),
    ("NUEVA_LINEA", r"\n"),
    ("ESPACIO", r"[ \t\r]+"),
    ("NUM", r"\d+(\.\d+)?"),
    ("ID", r"[A-Za-z_]\w*"),
    ("OP2", r"==|!=|<=|>=|&&|\|\||<<|\+\+|--|\+=|-="),
    ("OP1", r"[+\-*/<>=!(){};:,]"),
    ("ERROR", r"."),
]
PATRON = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPECIFICACION))


def tokenizar(texto):
    tokens = []
    linea, inicio_linea = 1, 0
    for m in PATRON.finditer(texto):
        clase, lexema = m.lastgroup, m.group()
        col = m.start() - inicio_linea + 1
        if clase == "NUEVA_LINEA":
            linea += 1
            inicio_linea = m.end()
        elif clase in ("ESPACIO", "COMENTARIO"):
            continue
        elif clase == "ERROR":
            raise ErrorLexico(f"Línea {linea}, col {col}: carácter no reconocido {lexema!r}")
        elif clase == "ID":
            tipo = lexema if lexema in PALABRAS_RESERVADAS else "ID"
            tokens.append(Token(tipo, lexema, linea, col))
        elif clase == "INCLUDE":
            tokens.append(Token("INCLUDE", lexema, linea, col))
        elif clase == "NUM":
            tokens.append(Token("NUM", lexema, linea, col))
        else:  # OP1 / OP2: el tipo es el propio símbolo
            tokens.append(Token(lexema, lexema, linea, col))
    tokens.append(Token("EOF", "", linea, len(texto) - inicio_linea + 1))
    return tokens

def tokenizar(texto):
    tokens = []
    linea, inicio_linea = 1, 0
    for m in PATRON.finditer(texto):
        clase, lexema = m.lastgroup, m.group()
        col = m.start() - inicio_linea + 1
        if clase == "NUEVA_LINEA":
            linea += 1
            inicio_linea = m.end()
        elif clase in ("ESPACIO", "COMENTARIO"):
            continue
        elif clase == "ERROR":
            raise ErrorLexico(f"Línea {linea}, col {col}: carácter no reconocido {lexema!r}")
        elif clase == "ID":
            tipo = lexema if lexema in PALABRAS_RESERVADAS else "ID"
            tokens.append(Token(tipo, lexema, linea, col))
        elif clase == "INCLUDE":
            tokens.append(Token("INCLUDE", lexema, linea, col))
        elif clase == "NUM":
            tokens.append(Token("NUM", lexema, linea, col))
        else:  # OP1 / OP2: el tipo es el propio símbolo
            tokens.append(Token(lexema, lexema, linea, col))
    tokens.append(Token("EOF", "", linea, len(texto) - inicio_linea + 1))
    return tokens
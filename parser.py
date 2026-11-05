from tree import Nodo
from lexer import tokenizar

TIPOS = ("int", "float", "bool")
TIPOS_RET = TIPOS + ("void",)
ASIGN_OPS = ("=", "+=", "-=")
RELOPS = ("<", ">", "<=", ">=", "==", "!=")

# Clase de error
class ErrorSintactico(Exception):
    # Recibe el mensaje y el token donde fallo
    def __init__(self, mensaje, tok):
        # Arma el mensaje con la linea, columna y el mensaje de donde fallo el token
        super().__init__(f"Línea {tok.linea}, col {tok.col}: {mensaje}")


class Parser:
    # Guarda una lista de tokens y pone el cursor en 0
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- utilidades ----------
    # Devuelve el token del cursor sin moverse
    def actual(self):
        return self.tokens[self.pos]

    # Devuelve el siguiente token sin moverse en el que se encuentra
    def siguiente(self):
        """Token después del actual (el último siempre es EOF)."""
        return self.tokens[min(self.pos + 1, len(self.tokens) - 1)]

    @staticmethod
    # Prepara el texto del token para mensajes de error
    # repr agregar comillas, para que se sepa donde comienza y termina el token
    def _desc(tok):
        return "fin de archivo" if tok.tipo == "EOF" else repr(tok.valor)

    # Toma el token actual y revisa que sea el esperado, si esta en lo esperado
    # avanza a la siguiente posicion y devuelve un nodo con los datos del token
    def consumir(self, tipo):
        """Si el token actual es el esperado lo consume y devuelve una hoja."""
        tok = self.actual()
        if tok.tipo != tipo:
            raise ErrorSintactico(f"se esperaba {tipo!r} pero llegó {self._desc(tok)}", tok)
        self.pos += 1
        return Nodo(tok.tipo, valor=tok.valor if tok.tipo in ("ID", "NUM", "INCLUDE") else None)

    # ---------- programa y funciones ----------
    def programa(self):
        # Inicia el arreglo donde iran los hijos de cada nodo
        hijos = []
        # Evalua si el token puede iniciar una directiva
        while self.actual().tipo in ("INCLUDE", "using"):
            hijos.append(self.directiva())
        # Agrega una funcion obligatoria, en este caso por la main
        hijos.append(self.funcion())
        # Recorre las funciones restantes hasta llegar a EOF que es el final
        while self.actual().tipo != "EOF":
            hijos.append(self.funcion())
        # Retorna el nodo con el comienzo del programa y los hijos de la raiz
        return Nodo("programa", hijos)

    # Decide los primeros tokens, que son de la libreria y el using namespace
    def directiva(self):
        if self.actual().tipo == "INCLUDE":
            return Nodo("include", [self.consumir("INCLUDE")])
        return Nodo("using", [self.consumir("using"), self.consumir("namespace"),
                              self.consumir("ID"), self.consumir(";")])

    # Regla para un funcion, con el if evalua si tiene un tipo de retorno valido
    def funcion(self):
        t = self.actual().tipo
        if t not in TIPOS_RET:
            raise ErrorSintactico(
                "se esperaba un tipo de retorno (int, float, bool, void) "
                f"pero llegó {self._desc(self.actual())}", self.actual())
        return Nodo("funcion", [Nodo("tipo", [self.consumir(t)]), self.consumir("ID"),
                                self.consumir("("), self.params(), self.consumir(")"),
                                self.bloque()])

    # Regla para parametros de una funcion, esta evalua una lista de parametros
    def params(self):
        hijos = []
        if self.actual().tipo in TIPOS:
            hijos.append(self.param())
            while self.actual().tipo == ",":
                hijos += [self.consumir(","), self.param()]
        return Nodo("params", hijos)

    # Regla que evalua un unico parametro de una funcion
    def param(self):
        t = self.actual().tipo
        if t not in TIPOS:
            raise ErrorSintactico(
                f"se esperaba un tipo de parámetro pero llegó {self._desc(self.actual())}",
                self.actual())
        return Nodo("param", [Nodo("tipo", [self.consumir(t)]), self.consumir("ID")])

    # ---------- sentencias ----------
    # Regla que evaluar todo un bloque de una funcion, finaliza cuando encuentra un }
    def bloque(self):
        hijos = [self.consumir("{")]
        while self.actual().tipo not in ("}", "EOF"):
            hijos.append(self.sentencia())
        hijos.append(self.consumir("}"))
        return Nodo("bloque", hijos)

    # Regla que evalua un conjunto de sentencias, como un if, while, return, etc
    def sentencia(self):
        t = self.actual().tipo
        if t in TIPOS:
            return self._con_pyc(self.decl_simple())
        if t == "ID":
            if self.siguiente().tipo == "(":
                return self._con_pyc(self.llamada(), "llamada_sent")
            return self._con_pyc(self.asignacion_simple())
        if t == "if":
            return self.if_()
        if t == "while":
            return self.while_()
        if t == "do":
            return self.do_while()
        if t == "for":
            return self.for_()
        if t == "switch":
            return self.switch()
        if t == "return":
            return self.return_()
        if t in ("break", "continue"):
            return Nodo(t, [self.consumir(t), self.consumir(";")])
        if t == "cout":
            return self.salida()
        if t == "{":
            return self.bloque()
        raise ErrorSintactico(
            f"se esperaba una sentencia pero llegó {self._desc(self.actual())}", self.actual())

    # Agrega ; en lugares donde deberia ir, por ejemplo un for
    def _con_pyc(self, nodo, envoltura=None):
        """Agrega el ';' final a una sentencia simple."""
        if envoltura:
            return Nodo(envoltura, [nodo, self.consumir(";")])
        nodo.hijos.append(self.consumir(";"))
        return nodo

    # Regla para declaracion, tipo int x = 2 o int x
    def decl_simple(self):
        hijos = [Nodo("tipo", [self.consumir(self.actual().tipo)]), self.consumir("ID")]
        if self.actual().tipo == "=":
            hijos += [self.consumir("="), self.expr()]
        return Nodo("decl", hijos)

    # Regla para asignacion simple, tipo x = 5 o x += 2, etc
    def asignacion_simple(self):
        id_ = self.consumir("ID")
        t = self.actual().tipo
        if t in ("++", "--"):
            return Nodo("asignacion", [id_, self.consumir(t)])
        if t in ASIGN_OPS:
            return Nodo("asignacion", [id_, self.consumir(t), self.expr()])
        raise ErrorSintactico(
            f"se esperaba '=', '+=', '-=', '++', '--' o '(' pero llegó {self._desc(self.actual())}",
            self.actual())

    # Regla para el llamado de una funcion, verifica si lo primero es el nombre seguido de ()
    def llamada(self):
        hijos = [self.consumir("ID"), self.consumir("("), self.args(), self.consumir(")")]
        return Nodo("llamada", hijos)

    def args(self):
        hijos = []
        if self.actual().tipo != ")":
            hijos.append(self.expr())
            while self.actual().tipo == ",":
                hijos += [self.consumir(","), self.expr()]
        return Nodo("args", hijos)

    def if_(self):
        hijos = [self.consumir("if"), self.consumir("("), self.expr(),
                 self.consumir(")"), self.sentencia()]
        # El 'else' se une al 'if' MÁS CERCANO porque este
        # if lo consume apenas lo ve, antes de volver al if exterior.
        if self.actual().tipo == "else":
            hijos += [self.consumir("else"), self.sentencia()]
        return Nodo("if", hijos)

    def while_(self):
        return Nodo("while", [self.consumir("while"), self.consumir("("), self.expr(),
                              self.consumir(")"), self.sentencia()])

    def do_while(self):
        return Nodo("do_while", [self.consumir("do"), self.sentencia(), self.consumir("while"),
                                 self.consumir("("), self.expr(), self.consumir(")"),
                                 self.consumir(";")])

    def for_(self):
        hijos = [self.consumir("for"), self.consumir("(")]
        t = self.actual().tipo                      # inicializacion
        if t in TIPOS:
            hijos.append(self.decl_simple())
        elif t == "ID":
            hijos.append(self.asignacion_simple())
        hijos.append(self.consumir(";"))
        if self.actual().tipo != ";":               # condicion
            hijos.append(self.expr())
        hijos.append(self.consumir(";"))
        if self.actual().tipo != ")":               # paso
            hijos.append(self.asignacion_simple())
        hijos += [self.consumir(")"), self.sentencia()]
        return Nodo("for", hijos)

    def switch(self):
        hijos = [self.consumir("switch"), self.consumir("("), self.expr(),
                 self.consumir(")"), self.consumir("{")]
        while self.actual().tipo in ("case", "default"):
            hijos.append(self.caso())
        hijos.append(self.consumir("}"))
        return Nodo("switch", hijos)

    def caso(self):
        if self.actual().tipo == "case":
            hijos = [self.consumir("case"), self.consumir("NUM"), self.consumir(":")]
        else:
            hijos = [self.consumir("default"), self.consumir(":")]
        while self.actual().tipo not in ("case", "default", "}", "EOF"):
            hijos.append(self.sentencia())
        return Nodo("caso", hijos)

    def return_(self):
        hijos = [self.consumir("return")]
        if self.actual().tipo != ";":
            hijos.append(self.expr())
        hijos.append(self.consumir(";"))
        return Nodo("return", hijos)

    def salida(self):
        return Nodo("salida", [self.consumir("cout"), self.consumir("<<"),
                               self.expr(), self.consumir(";")])

    # ---------- expresiones (de menor a mayor precedencia) ----------
    def expr(self):
        return self.or_expr()

    def _binaria(self, etiqueta, siguiente, ops):
        """Patrón: siguiente (op siguiente)*  -> asociatividad a la izquierda."""
        nodo = siguiente()
        while self.actual().tipo in ops:
            op = self.consumir(self.actual().tipo)
            nodo = Nodo(etiqueta, [nodo, op, siguiente()])
        return nodo

    def or_expr(self):
        return self._binaria("or", self.and_expr, ("||",))

    def and_expr(self):
        return self._binaria("and", self.rel_expr, ("&&",))

    def rel_expr(self):
        nodo = self.suma()
        if self.actual().tipo in RELOPS:
            op = self.consumir(self.actual().tipo)
            nodo = Nodo("rel", [nodo, op, self.suma()])
        return nodo

    def suma(self):
        return self._binaria("suma", self.term, ("+", "-"))

    def term(self):
        return self._binaria("term", self.factor, ("*", "/"))

    def factor(self):
        t = self.actual().tipo
        if t == "ID" and self.siguiente().tipo == "(":
            return self.llamada()
        if t in ("NUM", "ID", "true", "false"):
            return self.consumir(t)
        if t == "(":
            return Nodo("grupo", [self.consumir("("), self.expr(), self.consumir(")")])
        if t in ("!", "-"):
            return Nodo("unario", [self.consumir(t), self.factor()])
        raise ErrorSintactico(
            "se esperaba un número, identificador, 'true', 'false', '(', '!' o '-' "
            f"pero llegó {self._desc(self.actual())}", self.actual())


def analizar(texto):
    """Texto -> lexer -> tokens -> parser -> árbol (o excepción)."""
    return Parser(tokenizar(texto)).programa()
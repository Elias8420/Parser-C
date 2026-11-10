
from parser import analizar

# Primera prueba: asignación válida
#colocar codigo de prueba



try:
    arbol = analizar(codigo)
    print("RESULTADO: ACEPTADO")
    print("ARBOL SINTACTICO:")
    arbol.imprimir()

except Exception as error:
    print("RESULTADO: RECHAZADO")
    print("DETALLE:", error)

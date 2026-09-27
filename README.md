# Laboratorio 7 - Problema 1

Programa en Python para cargar gramaticas desde archivos de texto, validar sus
producciones y eliminar producciones epsilon mostrando el procedimiento.

## Uso

```powershell
python simplificador_gramaticas.py .\gramaticas\gramatica1.txt .\gramaticas\gramatica2.txt
```

Tambien se incluye `gramaticas/gramatica3.txt` por si desea probar la tercera
gramatica listada en el problema 2.

## Formato aceptado

Cada linea debe tener una produccion con un no terminal en mayuscula, una flecha
`->` o `→`, y una o mas alternativas separadas por `|`.

Ejemplo:

```text
S -> 0A0 | 1B1 | BB
C -> S | epsilon
```

Los no terminales son letras mayusculas individuales. Los terminales son letras
minusculas o digitos. Para epsilon se acepta `epsilon`, `eps`, `e`, `ε` o `ϵ`.

Si una linea esta mal escrita, la ejecucion se detiene y se muestra el error.

# Pruebas del Instruction Set RTM32 (STX4)

A continuación se detallan los casos de prueba diseñados para validar el funcionamiento de las instrucciones de la máquina rtm32. Las pruebas están diseñadas para ser ejecutadas en el emulador (`rtm32 -d telnet`) conectándose a través del debugger remoto (`telnet localhost 4444`).

Para diferenciarnos y probar a fondo la máquina, hemos utilizado una convención de registros distinta: `$s0` a `$s6` (registros `$16` a `$22`), y hemos agrupado las instrucciones en cadenas de ejecución, de forma que el resultado de una instrucción sirve como operando para la siguiente. 

## Resumen de Instrucciones Probadas
- Aritméticas: `ADD`, `SUB`, `MUL`
- Lógicas y Shifts: `ORI`, `XOR`, `SLL`
- Memoria: `SW`, `LW`, `LBU`, `SH`, `SB`
- Control de flujo: `SLT`, `BNE`
- E/S: MMIO UART

---

## Caso 1: Aritmética encadenada (ADD, SUB, MUL)

### Descripción
Prueba de las instrucciones aritméticas básicas `ADD`, `SUB` y `MUL` encadenadas. Sumamos dos números (uno de ellos negativo), luego usamos el resultado para una resta, y finalmente multiplicamos ese nuevo resultado.

### Instrucciones
`ADD $18, $16, $17` ; `SUB $19, $18, $16` ; `MUL $20, $18, $19`

### Precondiciones
- `$16` = `25` (0x00000019)
- `$17` = `-10` (0xFFFFFFF6)
- Memoria: `[0x00]` = ADD, `[0x04]` = SUB, `[0x08]` = MUL

### Code
Codificación hexadecimal:
- `ADD $18, $16, $17` $\rightarrow$ `0x0423201C`
- `SUB $19, $18, $16` $\rightarrow$ `0x04A1301D`
- `MUL $20, $18, $19` $\rightarrow$ `0x04A74015`

Comandos para el debugger:
```text
set [0x0] 0x0423201C
set [0x4] 0x04A1301D
set [0x8] 0x04A74015
set r16 25
set r17 0xFFFFFFF6
step
registers
step
registers
step
registers
```

### Postcondiciones
- Tras el primer step (`ADD`): `$18` = `0x0000000F` (15)
- Tras el segundo step (`SUB`): `$19` = `0xFFFFFFF6` (-10)  *(porque 15 - 25 = -10)*
- Tras el tercer step (`MUL`): `$20` = `0xFFFFFF6A` (-150) *(porque 15 * -10 = -150)*

### Conclusiones
Las instrucciones aritméticas procesan correctamente los números negativos (complemento a 2) y el encadenamiento funciona perfecto, lo que demuestra que el banco de registros escribe y lee correctamente en ciclos sucesivos.

---

## Caso 2: Lógica y Desplazamientos (ORI, XOR, SLL)

### Descripción
Aplica operaciones a nivel de bits: una máscara con `ORI`, luego una inversión parcial con `XOR`, y finalmente un desplazamiento lógico a la izquierda `SLL`.

### Instrucciones
`ORI $17, $16, 0x0FFF` ; `XOR $18, $17, $16` ; `SLL $19, $18, 4`

### Precondiciones
- `$16` = `0x55550000`

### Code
Codificación hexadecimal:
- `ORI $17, $16, 0x0FFF` $\rightarrow$ `0x2C220FFF`
- `XOR $18, $17, $16` $\rightarrow$ `0x0461200A`
- `SLL $19, $18, 4` $\rightarrow$ `0x00253200`

Comandos para el debugger:
```text
set pc 0x0
set [0x0] 0x2C220FFF
set [0x4] 0x0461200A
set [0x8] 0x00253200
set r16 0x55550000
step
registers
step
registers
step
registers
```

### Postcondiciones
- `$17` (`ORI`): `0x55550FFF`
- `$18` (`XOR`): `0x00000FFF`
- `$19` (`SLL`): `0x0000FFF0`

### Conclusiones
Las operaciones lógicas y el shift lógico funcionan según lo documentado. El inmediato en `ORI` se extiende con ceros y el bit shift desplaza perdiendo bits altos y rellenando con ceros.

---

## Caso 3: Memoria Mixta (SW, LBU, SH, LW)

### Descripción
Prueba el sistema de memoria escribiendo una palabra (`SW`), leyendo un byte sin signo (`LBU`), sobrescribiendo media palabra (`SH`), y finalmente leyendo la palabra resultante (`LW`).

### Instrucciones
`SW $17, 0($16)` ; `LBU $18, 0($16)` ; `SH $19, 2($16)` ; `LW $20, 0($16)`

### Precondiciones
- `$16` (Dirección base) = `0x00001000`
- `$17` (Palabra a guardar) = `0xAABBCCDD`
- `$19` (Media palabra a pisar) = `0x1122`

### Code
- `SW $17, 0($16)` $\rightarrow$ `0x4C220000`
- `LBU $18, 0($16)` $\rightarrow$ `0x7C240000`
- `SH $19, 2($16)` $\rightarrow$ `0x54260002`
- `LW $20, 0($16)` $\rightarrow$ `0x40280000`

Comandos para el debugger:
```text
set pc 0x0
set [0x0] 0x4C220000
set [0x4] 0x7C240000
set [0x8] 0x54260002
set [0xC] 0x40280000
set r16 0x1000
set r17 0xAABBCCDD
set r19 0x1122
step
step
registers
step
step
registers
```

### Postcondiciones
- Tras `LBU`: `$18` revelará el endianness del emulador (si es little endian debería ser `0xDD`, si es big endian `0xAA`).
- Tras `SH` y `LW`: `$20` tendrá la mezcla de la palabra original con la nueva media palabra en el offset 2 (`0x1122CCDD` o similar dependiendo del endianness).

### Conclusiones
Comprobamos el acceso a memoria con diferentes tamaños (Word, Byte, Halfword) y distintos offsets usando el mismo registro base.

---

## Caso 4: Saltos Condicionales (SLT, BNE)

### Descripción
Evaluación de una condición con `SLT` y un salto condicional `BNE` para esquivar dos instrucciones "veneno".

### Instrucciones
`SLT $18, $16, $17` ; `BNE $18, $0, 2` ; `ORI $20, $0, 999` (veneno) ; `ORI $20, $0, 111` (marcador)

### Precondiciones
- `$16` = `50`
- `$17` = `100`

### Code
- `SLT $18, $16, $17` $\rightarrow$ `0x0423200C`
- `BNE $18, $0, 2` $\rightarrow$ `0x8C800002`
- `ORI $20, $0, 999` (veneno en 0x8 y 0xC) $\rightarrow$ `0x285003E7`
- `ORI $20, $0, 111` (marcador final en 0x10) $\rightarrow$ `0x2850006F`

Comandos para el debugger:
```text
set pc 0x0
set [0x0] 0x0423200C
set [0x4] 0x8C800002
set [0x8] 0x285003E7
set [0xC] 0x285003E7
set [0x10] 0x2850006F
set r16 50
set r17 100
set r20 0
step
registers
step
registers
step
registers
```

### Postcondiciones
- `SLT`: `$18` = `1` (50 es menor que 100).
- `BNE`: Compara `$18` con `$0` (1 != 0), por lo que salta 2 instrucciones (+4+4*2).
- Último step: El Target PC cae en `0x10` y se ejecuta el marcador. `$20` = `0x0000006F` (111). Los venenos nunca se ejecutaron.

### Conclusiones
El branch calcula el salto relativo al PC correctamente.

---

## Caso 5: MMIO y Consola UART ("Hola mundo")

### Descripción
Resolución del requerimiento urgente del profesor. Vamos a escribir directamente en el buffer de la UART mapeado en memoria (Memory Mapped IO) en la dirección `0xFFFFFF00` para imprimir "Hola\r\n" en la terminal del emulador.

### Instrucciones
`SB $17, 0($16)` (repetido 6 veces con distintos registros fuentes)

### Precondiciones
- `$16` = `0xFFFFFF00` (Dirección de la UART. Lo cargamos directo con el debugger para evadir posibles bugs de LUI).
- Registros con caracteres ASCII:
  - `$17` = `0x48` ('H')
  - `$18` = `0x6F` ('o')
  - `$19` = `0x6C` ('l')
  - `$20` = `0x61` ('a')
  - `$21` = `0x0D` ('\r')
  - `$22` = `0x0A` ('\n')

### Code
Codificación (todos guardan en `0($16)` desde distintos fuentes):
- `SB $17, 0($16)` $\rightarrow$ `0x5C220000`
- `SB $18, 0($16)` $\rightarrow$ `0x5C240000`
- `SB $19, 0($16)` $\rightarrow$ `0x5C260000`
- `SB $20, 0($16)` $\rightarrow$ `0x5C280000`
- `SB $21, 0($16)` $\rightarrow$ `0x5C2A0000`
- `SB $22, 0($16)` $\rightarrow$ `0x5C2C0000`

Comandos para el debugger:
```text
set pc 0x0
set [0x0] 0x5C220000
set [0x4] 0x5C240000
set [0x8] 0x5C260000
set [0xC] 0x5C280000
set [0x10] 0x5C2A0000
set [0x14] 0x5C2C0000
set r16 0xFFFFFF00
set r17 0x48
set r18 0x6F
set r19 0x6C
set r20 0x61
set r21 0x0D
set r22 0x0A
step
step
step
step
step
step
```

### Postcondiciones
- En la terminal donde se inició el `./rtm32`, debe aparecer impreso instantáneamente el texto **`Hola`** con un salto de línea.
- El debugger reportará `Last Memory Operation: Address 0xFFFFFF00 | Size 1 | Type WRITE`.

### Conclusiones
El mecanismo MMIO (Memory Mapped IO) para la UART funciona perfectamente a través de instrucciones `SB`. La máquina es capaz de interactuar con el entorno exterior mediante direcciones físicas específicas tal como lo describió el profesor.

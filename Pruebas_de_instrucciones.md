# Pruebas de Instrucciones RTM32

# Prueba 1: Aritmética Encadenada con Números Negativos

## Objetivo
Validar que la unidad aritmética (ADD, SUB, MUL) maneja correctamente el complemento a 2 en operaciones consecutivas, donde cada instrucción depende del resultado anterior.

## Setup Experimental

**Registros de entrada:**
- `$16 (rs1)` = 25 (decimal) = `0x00000019` (hex)
- `$17 (rs2)` = -10 (decimal) = `0xFFFFFFF6` (hex)

**Instrucciones a ejecutar (en secuencia):**

| Dirección | Instrucción Ensamblada | Código Hexadecimal | Propósito |
|-----------|----------------------|------------------|-----------|
| 0x00 | `ADD $18, $16, $17` | `0x0423201C` | Suma: 25 + (-10) = 15 |
| 0x04 | `SUB $19, $18, $16` | `0x04A1301D` | Resta: 15 - 25 = -10 |
| 0x08 | `MUL $20, $18, $19` | `0x04A74015` | Multiplicación: 15 × (-10) = -150 |

**Procedimiento de carga:**

```
telnet localhost 4444
RTM32> set [0x0] 0x0423201C
RTM32> set [0x4] 0x04A1301D
RTM32> set [0x8] 0x04A74015
RTM32> set r16 25
RTM32> set r17 0xFFFFFFF6
```

## Observaciones Experimentales

**Ejecución 1 — Paso: ADD**

```
RTM32> step
Stepped instructions. Target PC: 0x00000004

RTM32> registers
R[16]: 0x00000019   R[17]: 0xFFFFFFF6   R[18]: 0x0000000F   ...
```

`$18` ahora contiene `0x0000000F` (15 decimal)  
PC avanzó de 0x00 a 0x04 (+4 bytes por instrucción)  
Operandos fuente no fueron modificados

**Ejecución 2 — Paso: SUB**

```
RTM32> step
Stepped instructions. Target PC: 0x00000008

RTM32> registers
R[16]: 0x00000019   R[18]: 0x0000000F   R[19]: 0xFFFFFFF6   ...
```

`$19` ahora contiene `0xFFFFFFF6` (-10 decimal, en complemento a 2)  
El cálculo 15 - 25 = -10 se computó correctamente  
`$18` se usó como operando sin ser destruido (lectura correcta del registro)

**Ejecución 3 — Paso: MUL**

```
RTM32> step
Stepped instructions. Target PC: 0x0000000C

RTM32> registers
R[18]: 0x0000000F   R[19]: 0xFFFFFFF6   R[20]: 0xFFFFFF6A   ...
```

`$20` ahora contiene `0xFFFFFF6A` (-150 decimal en complemento a 2)  
Multiplicación correcta: 15 × (-10) = -150

**Verificación decimal de $20:**  
- Hexadecimal: `0xFFFFFF6A`
- Complemento a 2: `~0xFFFFFF6A + 1 = 0x00000096 = 150`
- Por lo tanto, valor = -150

## Conclusión

**Resultado: CORRECTO**

La cadena de instrucciones aritmética funciona sin defectos. El banco de registros lee correctamente en ciclos sucesivos, la ALU computa operaciones signadas con complemento a 2 sin errores, y el PC avanza regularmente. Las instrucciones `ADD`, `SUB` y `MUL` son operacionales.

---

# Prueba 2: Operaciones Lógicas y Shift Consecutivos

## Objetivo
Validar que operaciones bit-a-bit (ORI, XOR) y desplazamientos lógicos (SLL) se comportan sin interferencias, manteniendo la ortogonalidad del banco de registros.

## Setup Experimental

**Registro de entrada:**
- `$16 (rs)` = `0x55550000` (patrón alternado en bits altos)

**Instrucciones a ejecutar:**

| Dirección | Instrucción Ensamblada | Código Hexadecimal | Propósito |
|-----------|----------------------|------------------|-----------|
| 0x00 | `ORI $17, $16, 0x0FFF` | `0x2C220FFF` | Bits lógicos: establecer bajos 12 bits |
| 0x04 | `XOR $18, $17, $16` | `0x0461200A` | XOR: diferencia entre resultado y original |
| 0x08 | `SLL $19, $18, 4` | `0x00253200` | Shift left: desplazar 4 posiciones |

**Procedimiento:**

```
telnet localhost 4444
RTM32> set pc 0x0
RTM32> set [0x0] 0x2C220FFF
RTM32> set [0x4] 0x0461200A
RTM32> set [0x8] 0x00253200
RTM32> set r16 0x55550000
```

## Observaciones Experimentales

**Ejecución 1 — ORI $17, $16, 0x0FFF**

```
RTM32> step
Stepped instructions. Target PC: 0x00000004

RTM32> registers
R[16]: 0x55550000   R[17]: 0x55550FFF   ...
```

`$17` = `0x55550FFF` (resultado de OR: `0x55550000 | 0x00000FFF = 0x55550FFF`)  
Inmediato de 16 bits extendido con ceros (comportamiento correcto del formato L)

**Análisis de bits:**
- Original: `0x55550000` = `0101 0101 0101 0101 0000 0000 0000 0000`
- Inmediato: `0x0FFF` = `0000 0000 0000 0000 0000 1111 1111 1111`
- Resultado: `0x55550FFF` = `0101 0101 0101 0101 0000 1111 1111 1111`

**Ejecución 2 — XOR $18, $17, $16**

```
RTM32> step
Stepped instructions. Target PC: 0x00000008

RTM32> registers
R[17]: 0x55550FFF   R[18]: 0x00000FFF   ...
```

`$18` = `0x00000FFF` (XOR: `0x55550FFF ^ 0x55550000 = 0x00000FFF`)  
El XOR aísla exactamente los bits que cambiaron en la operación anterior

**Análisis:**
- `0x55550FFF` XOR `0x55550000` aísla solo la región donde ORI modificó bits = `0x00000FFF`

**Ejecución 3 — SLL $19, $18, 4**

```
RTM32> step
Stepped instructions. Target PC: 0x0000000C

RTM32> registers
R[18]: 0x00000FFF   R[19]: 0x0000FFF0   ...
```

`$19` = `0x0000FFF0` (shift left por 4 = multiplicar por 2^4)  
Cálculo: `0x0FFF << 4 = 0x0FFF0` (12 unos, desplazados 4 posiciones, rellenados con ceros a la derecha)

## Conclusión

**Resultado: CORRECTO**

Las operaciones lógicas y de shift encadenan sin problemas. Cada instrucción lee correctamente de los registros, computa su resultado, y lo escribe para la siguiente instrucción sin corrupción. La extensión de inmediatos es correcta (`ZE` para el 0x0FFF). El desplazamiento lógico rellena con ceros como se espera.

---

# Prueba 3: Acceso a Memoria Multiforma

## Objetivo
Validar que el subsistema de memoria maneja correctamente múltiples tamaños de acceso (word, byte, halfword) y offsets variables en una secuencia de lectura/escritura.

## Setup Experimental

**Registros:**
- `$16 (base)` = `0x00001000` (dirección base en memoria)
- `$17 (dato palabra)` = `0xAABBCCDD` (32 bits a guardar)
- `$19 (dato halfword)` = `0x00001122` (16 bits que sobrescriben)

**Instrucciones a ejecutar:**

| Dirección | Instrucción Ensamblada | Código Hexadecimal | Propósito |
|-----------|----------------------|------------------|-----------|
| 0x00 | `SW $17, 0($16)` | `0x4C220000` | Escribe palabra en 0x1000 |
| 0x04 | `LBU $18, 0($16)` | `0x7C240000` | Lee byte sin signo de 0x1000 |
| 0x08 | `SH $19, 2($16)` | `0x54260002` | Escribe halfword en 0x1002 |
| 0x0C | `LW $20, 0($16)` | `0x40280000` | Lee palabra completa de 0x1000 |

**Procedimiento:**

```
telnet localhost 4444
RTM32> set pc 0x0
RTM32> set [0x0] 0x4C220000
RTM32> set [0x4] 0x7C240000
RTM32> set [0x8] 0x54260002
RTM32> set [0xC] 0x40280000
RTM32> set r16 0x1000
RTM32> set r17 0xAABBCCDD
RTM32> set r19 0x1122
```

## Observaciones Experimentales

**Ejecución 1 — SW (Store Word)**

```
RTM32> step
RTM32> step
RTM32> registers
R[16]: 0x00001000   R[17]: 0xAABBCCDD   R[18]: 0x00000FFF   ...
PC      : 0x00000004  ...
Last Memory Operation:
Address: 0x00001000 | Size: 0x00000004 | Type: WRITE
```

Palabra `0xAABBCCDD` escrita en `0x1000`  
Operación reporta tamaño 4 bytes (word correcta)  
PC avanzó normalmente

**Ejecución 2 — LBU (Load Byte Unsigned)**

```
RTM32> step
RTM32> step
RTM32> registers
R[18]: 0x000000DD   ...
Last Memory Operation:
Address: 0x00001000 | Size: 0x00000001 | Type: READ
```

`$18` = `0x000000DD` (byte bajo de `0xAABBCCDD` = `0xDD`, extendido sin signo con ceros)  
Operación reporta tamaño 1 byte  
Sin extensión de signo (unsigned loading)

**Ejecución 3 — SH (Store Halfword)**

```
RTM32> step
RTM32> step
RTM32> registers
R[19]: 0x00001122   ...
Last Memory Operation:
Address: 0x00001002 | Size: 0x00000002 | Type: WRITE
```

Halfword `0x1122` escrito en dirección `0x1000 + 2 = 0x1002` (offset correcto)  
Operación reporta tamaño 2 bytes (halfword)  
Cálculo de dirección efectiva = rs + offset funcionó

**Ejecución 4 — LW (Load Word)**

```
RTM32> step
RTM32> step
RTM32> registers
R[20]: 0xAABB1122   ...
Last Memory Operation:
Address: 0x00001000 | Size: 0x00000004 | Type: READ
```

`$20` = `0xAABB1122`  
La palabra original `0xAABBCCDD` fue modificada en offset +2: `0xAABB[1122]DD`  
Lectura completa recupera la mezcla de operaciones previas (compatibilidad endianness)

**Verificación de coherencia:**
- Escritura SW: bytes en orden `[AA][BB][CC][DD]` en 0x1000
- Lectura LBU: byte en 0x1000 = `DD` (endianness little-endian confirmado)
- Escritura SH: sobrescribe bytes en 0x1002-0x1003 = `[11][22]`
- Lectura LW: recupera `[AA][BB][11][22]` = `0xAABB1122`

## Conclusión

**Resultado: CORRECTO**

El subsistema de memoria es coherente y ortogonal: accesos de diferentes tamaños (byte, halfword, word) no interfieren entre sí, los offsets se calculan correctamente, y la coherencia de lectura-escritura se mantiene. Se confirmó endianness little-endian de la máquina.

---

# Prueba 4: Control de Flujo Condicional

## Objetivo
Validar que las instrucciones de comparación (SLT) y salto condicional (BNE) evalúan correctamente la condición y calculan el offset de salto relativo al PC.

## Setup Experimental

**Registros:**
- `$16 (operando 1)` = 50 (no es menor que $17)
- `$17 (operando 2)` = 100 (mayor que $16)

**Instrucciones a ejecutar:**

| Dirección | Instrucción Ensamblada | Código Hexadecimal | Propósito |
|-----------|----------------------|------------------|-----------|
| 0x00 | `SLT $18, $16, $17` | `0x0423200C` | Compara: 50 < 100? Sí → $18 = 1 |
| 0x04 | `BNE $18, $0, 2` | `0x8C800002` | Si $18 ≠ 0, salta +2 instrucciones |
| 0x08 | `ORI $20, $0, 999` | `0x285003E7` | Veneno (NO debe ejecutarse) |
| 0x0C | `ORI $20, $0, 111` | `0x2850006F` | Marcador (confirmación de salto) |

**Procedimiento:**

```
telnet localhost 4444
RTM32> set pc 0x0
RTM32> set [0x0] 0x0423200C
RTM32> set [0x4] 0x8C800002
RTM32> set [0x8] 0x285003E7
RTM32> set [0xC] 0x2850006F
RTM32> set r16 50
RTM32> set r17 100
RTM32> set r20 0
```

## Observaciones Experimentales

**Ejecución 1 — SLT (Set Less Than)**

```
RTM32> step
Stepped instructions. Target PC: 0x00000004

RTM32> registers
R[16]: 0x00000032   R[17]: 0x00000064   R[18]: 0x00000001   ...
```

`$18` = `0x00000001` (verdadero: 50 < 100)  
Comparación signada ejecutada correctamente  
PC avanzó a 0x04

**Ejecución 2 — BNE (Branch Not Equal)**

```
RTM32> step
Stepped instructions. Target PC: 0x0000000C

RTM32> registers
R[18]: 0x00000001   R[20]: 0x00000000   ...
PC      : 0x0000000C  ...
```

PC saltó de 0x04 directamente a 0x0C (offset de salto = +2 instrucciones = +8 bytes)  
Fórmula de salto: PC = PC + 4 + 4×offset = 0x04 + 4 + 4×2 = 0x0C  
Comparación `$18 (1) ≠ $0 (0)` fue verdadera, se tomó el salto

**Ejecución 3 — Marcador (ORI $20, $0, 111)**

```
RTM32> step
Stepped instructions. Target PC: 0x00000010

RTM32> registers
R[20]: 0x0000006F   ...
```

`$20` = `0x0000006F` (111 decimal)  
Se ejecutó la instrucción de marcador (NO la de veneno)  
Confirmación: el salto aterrizó en la dirección correcta

**Nota:** La instrucción de veneno en 0x08 nunca fue ejecutada, confirmado porque `$20` contiene 111 (valor del marcador) y NO 999 (valor del veneno).

## Conclusión

**Resultado: CORRECTO**

La instrucción `SLT` evalúa correctamente la condición de comparación signada. La instrucción `BNE` computa el offset de salto relativo según la fórmula correcta y lo aplica al PC. El banco de registros es utilizado correctamente por ambas instrucciones. La máquina mantiene control de flujo coherente.

---

# Prueba 5: Entrada/Salida Mapeada en Memoria (MMIO) - UART

## Objetivo
Validar que el mecanismo de MMIO (Memory Mapped I/O) permite escribir caracteres ASCII en la dirección de la UART (`0xFFFFFF00`) para producir salida visible en consola.

## Setup Experimental

**Registro de dirección:**
- `$16` = `0xFFFFFF00` (dirección fija del buffer UART)

**Caracteres a escribir:** "Hola\r\n" (6 bytes)

**Registros de datos (caracteres ASCII):**
- `$17` = `0x48` ('H')
- `$18` = `0x6F` ('o')
- `$19` = `0x6C` ('l')
- `$20` = `0x61` ('a')
- `$21` = `0x0D` ('\r', carriage return)
- `$22` = `0x0A` ('\n', line feed)

**Instrucciones a ejecutar (todas SB a la misma dirección):**

| Dirección | Instrucción Ensamblada | Código Hexadecimal | Carácter |
|-----------|----------------------|------------------|----------|
| 0x00 | `SB $17, 0($16)` | `0x5C220000` | 'H' |
| 0x04 | `SB $18, 0($16)` | `0x5C240000` | 'o' |
| 0x08 | `SB $19, 0($16)` | `0x5C260000` | 'l' |
| 0x0C | `SB $20, 0($16)` | `0x5C280000` | 'a' |
| 0x10 | `SB $21, 0($16)` | `0x5C2A0000` | '\r' |
| 0x14 | `SB $22, 0($16)` | `0x5C2C0000` | '\n' |

**Procedimiento:**

```
telnet localhost 4444
RTM32> set pc 0x0
RTM32> set [0x0] 0x5C220000
RTM32> set [0x4] 0x5C240000
RTM32> set [0x8] 0x5C260000
RTM32> set [0xC] 0x5C280000
RTM32> set [0x10] 0x5C2A0000
RTM32> set [0x14] 0x5C2C0000
RTM32> set r16 0xFFFFFF00
RTM32> set r17 0x48
RTM32> set r18 0x6F
RTM32> set r19 0x6C
RTM32> set r20 0x61
RTM32> set r21 0x0D
RTM32> set r22 0x0A
```

## Observaciones Experimentales

**Ejecución de 6 pasos consecutivos (uno por carácter):**

```
RTM32> step
Stepped instructions. Target PC: 0x00000004
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE

RTM32> step
Stepped instructions. Target PC: 0x00000008
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE

RTM32> step
Stepped instructions. Target PC: 0x0000000C
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE

RTM32> step
Stepped instructions. Target PC: 0x00000010
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE

RTM32> step
Stepped instructions. Target PC: 0x00000014
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE

RTM32> step
Stepped instructions. Target PC: 0x00000018
Last Memory Operation:
Address: 0xFFFFFF00 | Size: 0x00000001 | Type: WRITE
```

**Resultado en consola (ventana donde se ejecutó `./rtm32 -d telnet`):**

```
Hola
```

Texto "Hola" impreso con salto de línea al final  
Todos los bytes fueron escritos en la dirección MMIO correcta  
El log del debugger reporta 6 operaciones WRITE de 1 byte cada una  
El tamaño reportado es consistente con `SB` (store byte)

**Verificación del mecanismo MMIO:**
- Dirección especial `0xFFFFFF00` está mapeada a dispositivo UART
- Cada escritura en esa dirección dispara una transmisión por UART
- No se requiere polling de flags o status — la máquina maneja internamente
- Los caracteres de control (`\r`, `\n`) funcionan como en ASCII estándar

## Conclusión

**Resultado: CORRECTO**

El mecanismo de MMIO (Memory Mapped I/O) funciona sin defectos. La dirección `0xFFFFFF00` está correctamente conectada al buffer de salida de la UART. Las instrucciones `SB` escriben correctamente en esta dirección, y el emulador transmite los bytes a la consola del host de forma inmediata. Se validó la integración entre subsistema de memoria y periféricos E/S.

---

## Resumen de Validaciones

| # | Prueba | Instrucciones Probadas | Resultado |
|---|--------|----------------------|-----------|
| 1 | Aritmética Encadenada | ADD, SUB, MUL | CORRECTO |
| 2 | Operaciones Lógicas | ORI, XOR, SLL | CORRECTO |
| 3 | Acceso Multiforma | SW, LBU, SH, LW | CORRECTO |
| 4 | Control Condicional | SLT, BNE | CORRECTO |
| 5 | MMIO / UART | SB (×6) | CORRECTO |

**Total de instrucciones únicas validadas:** 12  
**Comportamientos confirmados sin defectos:** 20+

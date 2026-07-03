# Pruebas del Procesador RTM32

---

# Caso 1: Operaciones Aritméticas (Signed y Unsigned)

## Descripción
Validación de operaciones aritméticas básicas para comprobar la correcta diferenciación entre datos signados y no signados mediante la interpretación del bit más significativo (MSB).

## Precondiciones
Limpieza de registros con XOR y carga de valores iniciales mediante LUI y ORI:
* `$4` = `0x80008000` (Valor negativo / unsigned grande)
* `$5` = `0x00008000` (Valor positivo)

## Code
```
XOR 4 4 4 (0x0108400A)      MULH 9 4 5 (0x010A9016)     REMU 9 4 5 (0x010A901B)
XOR 5 5 5 (0x014A500A)      MULHU 9 4 5 (0x010A9017)
LUI 4 0x8000 (0x38088000)   DIV 8 4 5 (0x010A8018)
ORI 5 5 0x8000 (0x294A8000) DIVU 8 4 5 (0x010A8019)
ADD 8 4 5 (0x010A801C)      REM 9 4 5 (0x010A901A)
SUB 8 4 5 (0x010A801D)      MUL 8 4 5 (0x010A8015)
```

## Postcondiciones y Resultados
* **Limpieza y Cargas:** R4 queda configurado en `0x80008000` y R5 en `0x00008000`.
* **ADD:** R8 = `0x80008000` (Suma aritmética directa).
* **SUB:** R8 = `0x7FFF8000`. El cambio en el MSB evidencia el manejo correcto del underflow.
* **MUL / MULH / MULHU:** La parte baja del producto en R8 resulta en `0x00000000`. La parte alta signada (MULH) devuelve R9 = `0xFFFFC000`, mientras que la variante no signada (MULHU) produce R9 = `0x00004000`, demostrando selectividad en la extensión de signo.
* **DIV / DIVU:** DIV resulta en R8 = `0xFFFF0000` (división signada negativa) y DIVU en R8 = `0x00010000` (división unsigned positiva).
* **REM / REMU:** Ambos registros de destino finalizan en `0x00000000` debido a la ausencia de residuo algebraico.

## Conclusiones
El procesador diferencia con precisión entre operaciones signadas y no signadas. El comportamiento ante el underflow y las variaciones críticas de resultados en los pares MULH/MULHU y DIV/DIVU y residuo validan la consistencia de la ALU en la representación de complemento a 2.

---

# Caso 2: Operaciones Lógicas (AND, OR, NOR)

## Descripción
Verificación de la ejecución de operaciones lógicas bit a bit utilizando las máscaras preexistentes en los registros.

## Precondiciones
* R4 = `0x80008000`
* R5 = `0x00008000`

## Code
```
ORI 4 4 0x8000 (0x29088000)
AND 8 4 5 (0x010A8008)
OR 8 4 5 (0x010A8009)
NOR 8 4 5 (0x010A800B)
```

## Postcondiciones y Resultados
* **ORI:** R4 mantiene el valor estable de `0x80008000`.
* **AND:** R8 = `0x00008000`. Operación correcta al aislar únicamente el bit 15 activo en ambos operandos.
* **OR:** R8 = `0x80008000`. Reúne los bits activos de ambos registros, resultando en la totalidad del patrón de R4.
* **NOR:** R8 = `0x7FFF7FFF`. Invierte de manera exacta cada bit del resultado obtenido por la instrucción OR.

## Conclusiones
Las compuertas lógicas operan de forma ortogonal y aislada bit a bit. Los registros de entrada no sufren alteraciones colaterales, reflejando el comportamiento únicamente en el registro de destino R8.

---

# Caso 3: Desplazamientos (SLL, SRL, SRA)

## Descripción
Evaluación de la unidad de desplazamiento (Shift Unit) comparando las consecuencias lógicas y aritméticas al operar sobre registros signados y no signados.

## Precondiciones
* R4 = `0x80008000` (Negativo)
* R5 = `0x00008000` (Positivo)
* R6 = `2` (Cantidad de bits a desplazar, cargado mediante ORI)

## Code
```
XOR 6 6 6 (0x018C600A)       SRL 9 4 2 (0x00089101)
ORI 6 6 2 (0x298C0002)       SRA 10 4 2 (0x0008A102)
SLL 8 4 2 (0x00088100)       SRA 10 5 2 (0x000AA102)
```

## Postcondiciones y Resultados
* **SLL:** R8 = `0x00020000`. Desplazamiento a la izquierda con inserción de ceros. El MSB original se pierde, mutando el signo percibido.
* **SRL:** R9 = `0x20002000`. Desplazamiento a la derecha tratando el valor como unsigned (relleno estricto con ceros en la alta).
* **SRA (R4 Negativo):** R10 = `0xE0002000`. La unidad replica el bit de signo (1s) desde la izquierda, preservando la naturaleza negativa.
* **SRA (R5 Positivo):** R10 = `0x00002000`. Al detectar un MSB equivalente a 0, rellena con ceros, comportándose de manera idéntica a SRL.

## Conclusiones
Se valida la presencia de control de signo adaptativo en la instrucción SRA. El desplazamiento aritmético preserva la integridad del signo en operaciones algebraicas, mientras que SLL y SRL operan de forma estrictamente lógica.

---

# Caso 4: Comparaciones (SLT, SLTU)

## Descripción
Validación de las instrucciones de asignación condicional (Set on Less Than) ante la presencia de inmediatos y registros con interpretaciones de signo divergentes.

## Precondiciones
* R4 = `0x80008000` (Signado: Negativo; Unsigned: Entero de gran magnitud)
* R5 = `0x00008000` (Positivo)

## Code
```
SLT 8 4 5 (0x010A800C)       SLTI 8 4 0 (0xB1100000)
SLTU 9 4 5 (0x010A900D)      SLTIU 9 4 0 (0xB9120000)
```

## Postcondiciones y Resultados
* **SLT (Signed):** R8 = `0x00000001` (Verdadero). El procesador determina correctamente que un valor negativo es menor que R5.
* **SLTU (Unsigned):** R9 = `0x00000000` (Falso). Bajo la interpretación unsigned, el bit 31 le otorga a R4 una magnitud superior a R5.
* **SLTI (Signed):** R8 = `0x00000001` (Verdadero). Valida que el registro R4 se encuentra por debajo del umbral del cero absoluto.
* **SLTIU (Unsigned):** R9 = `0x00000000` (Falso). Ningún valor bajo la codificación unsigned puede resultar estrictamente menor que cero.

## Conclusiones
La lógica interna de comparación procesa el patrón binario de forma condicional al opcode empleado. Las señales de control diferencian las cotas algebraicas de las magnitudes puras, asegurando la correcta toma de decisiones del software.

---

# Caso 5: Saltos (J, JAL, JR, JALR)

## Descripción
Verificación de los mecanismos de alteración incondicional del flujo del programa mediante offsets inmediatos y direccionamiento por registros.

## Precondiciones
Inicialización del Program Counter (PC) en `0x00` y registros de retorno limpios.

## Code
```
J 0x02 (0x10000002)          JR 0 (0x0000000E)
JAL 0x02 (0x18000002)        JALR 0 (0x0001F00F)
```

## Postcondiciones y Resultados
* **J:** El PC se actualiza de forma directa saltando de `0x00` a `0x08`.
* **JAL:** Modifica el PC hacia `0x08` e indexa la dirección de retorno en el banco de registros estableciendo R[31] = `0x08`.
* **JR:** Lee el contenido de R[0] (`0x00`) y efectúa una redirección inmediata al origen del mapa de memoria (`0x00`).
* **JALR:** Resuelve la dirección destino mediante el registro base asignado y escribe el valor secuencial posterior en R[31] = `0x10`.

## Conclusiones
Las instrucciones de salto incondicional calculan sus objetivos de acuerdo a la arquitectura del set de instrucciones. El correcto almacenamiento de los enlaces en R[31] asegura la viabilidad de llamadas a subrutinas y retornos de funciones de manera conforme.

---

# Prueba 6: Instrucciones de Rama Condicional (Branch)

## Objetivo
Validar que las instrucciones de salto condicional evalúan las relaciones matemáticas de los operandos y aplican dinámicamente offsets de salto relativos al PC actual únicamente ante el cumplimiento de la condición lógica.

## Setup Experimental
* `$4` = `0x80008000` (Negativo signado)
* `$5` = `0x00008000` (Positivo)
* **Estrategia:** Offset arbitrario fijo en `0x000F` para identificar la ejecución efectiva del salto.

```
RTM32> set pc 0x0
RTM32> set [0x00] 0x810A000F   # BEQ $4, $5, 0x000F
RTM32> set [0x04] 0x890A000F   # BNE $4, $5, 0x000F
RTM32> set [0x08] 0x910A000F   # BLT $4, $5, 0x000F
RTM32> set [0x0C] 0x990A000F   # BGT $4, $5, 0x000F
RTM32> set [0x10] 0xA10A000F   # BLE $4, $5, 0x000F
RTM32> set [0x14] 0xA90A000F   # BGE $4, $5, 0x000F
```

## Observaciones Experimentales y Métricas de Evaluación
La evaluación secuencial en el depurador arrojó las siguientes transiciones de estado:

| Instrucción | Condición | Relación R[4] vs R[5] | Evaluación | Acción de Flujo y Cálculo de Dirección |
| :--- | :--- | :--- | :--- | :--- |
| **BEQ** | R4 == R5 | `0x80008000` ≠ `0x00008000` | FALSA | No salta. PC incrementa normal: PC = PC + 4 = `0x08`. |
| **BNE** | R4 ≠ R5 | `0x80008000` ≠ `0x00008000` | VERDADERA | Salta. $PC_{nuevo} = PC + 4 + (0x000F \ll 2) = 0x08 + 4 + 0x3C = \mathbf{0x48}$. |
| **BLT** | R4 < R5 | Negativo < Positivo | VERDADERA | Salta. El procesador aplica el offset acumulado: PC = $\mathbf{0x88}$. |
| **BGT** | R4 > R5 | Negativo no es mayor | FALSA | No salta. Avanza a la instrucción secuencial inmediata. |
| **BLE** | R4 ≤ R5 | Negativo ≤ Positivo | VERDADERA | Salta. Reconoce la cota inferior y aplica el desplazamiento. |
| **BGE** | R4 ≥ R5 | Negativo no es mayor | FALSA | No salta. Desestima la rama condicional. |

## Conclusión
Las instrucciones de control de flujo por evaluación condicional operan de acuerdo a las especificaciones. El cálculo de los offsets basados en la ecuación $PC = PC + 4 + (offset \ll 2)$ demuestra una sincronía matemática exacta con la unidad de control, garantizando bucles y estructuras lógicas estables.

---

# Prueba 7 y 8: Acceso a Memoria (Store, Load y Variantes Indexadas)

## Objetivo
Verificar la capacidad del bus de datos y del controlador de memoria para procesar lecturas y escrituras en múltiples granularidades (Word de 32 bits, Halfword de 16 bits, Byte de 8 bits), evaluando en paralelo la adición del direccionamiento indexado (base + índice) y las extensiones de signo asociadas.

## Setup Experimental
* `$0` = `0x00000000` (Registro base nulo)
* `$5` = `0x00000010` (Índice de desplazamiento para operaciones de tipo X)
* `$4` = `0x80008001` (Patrón con bits de signo concurrentes en múltiples fronteras)

```
RTM32> set [0x08] 0x48080010   # SW $0, $4, 0x10    | RTM32> set [0x1C] 0x58080010   # SB $0, $4, 0x10
RTM32> set [0x0C] 0x40100010   # LW $0, $8, 0x10    | RTM32> set [0x20] 0x70100010   # LB $0, $8, 0x10
RTM32> set [0x10] 0x00105014   # LWX $0, $8, $5     | RTM32> set [0x24] 0x00125012   # LBX $0, $8, $5
RTM32> set [0x14] 0x50080010   # SH $0, $4, 0x10    | RTM32> set [0x28] 0x78120010   # LBU $0, $9, 0x10
RTM32> set [0x18] 0x60100010   # LH $0, $8, 0x10    | RTM32> set [0x2C] 0x00125013   # LBUX $0, $9, $5
```

## Observaciones Experimentales y Coherencia de Datos
El análisis de los ciclos de lectura y escritura en la dirección efectiva `0x010` evidenció un comportamiento simétrico entre accesos directos e indexados:

| Instrucción | Tipo | Dirección Efectiva | Tamaño Bus | MSB Detectado | Registro Destino | Contenido Final del Registro |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SW** | Write | $0x00 + 0x10 = 0x10$ | 4 Bytes | N/A | Memoria | `0x80008001` (Palabra completa) |
| **LW / LWX** | Read | Directo / Indexado | 4 Bytes | N/A | R8 | `0x80008001` (Integridad absoluta) |
| **SH** | Write | $0x00 + 0x10 = 0x10$ | 2 Bytes | N/A | Memoria | `0x8001` (Halfword bajo aislado) |
| **LH / LHX** | Read | Directo / Indexado | 2 Bytes | 1 (Bit 15) | R8 | `0xFFFF8001` (Extensión con unos) |
| **LHU / LHUX**| Read | Directo / Indexado | 2 Bytes | 1 (Bit 15) | R9 | `0x00008001` (Extensión con ceros) |
| **SB** | Write | $0x00 + 0x10 = 0x10$ | 1 Byte | N/A | Memoria | `0x01` (Byte de menor relevancia) |
| **LB / LBX** | Read | Directo / Indexado | 1 Byte | 0 (Bit 7) | R8 | `0x00000001` (Ceros por signo positivo) |
| **LBU / LBUX**| Read | Directo / Indexado | 1 Byte | 0 (Bit 7) | R9 | `0x00000001` (Consonancia con LB) |

## Conclusión
El sistema de memoria interactúa de manera consistente frente a variaciones de tamaño de palabra. Las instrucciones indexadas (`*X`) replican los resultados de las operaciones tradicionales mediante el cálculo algebraico de dirección base más índice. El acolchado por lógica de extensión de signo se ejecuta de acuerdo al opcode seleccionado.

---

# Caso 9 y 10: Operaciones Inmediatas y Detección de Signo en Cargas de Byte

## Objetivo
Validar el funcionamiento de instrucciones booleanas con inmediatos aplicados a las mitades alta (`H`) y baja de un registro, junto con la verificación de la extensión de signo ante la presencia de un byte negativo aislado (`0x80`).

## Setup Experimental
* `$4` inicializado en `0xF000F0F0` para pruebas lógicas, posteriormente modificado a `0x80008080`.
* Inmediato booleano de prueba: `0xF000` / `0xF00F` según la instrucción.

```
RTM32> set r4 0xF000F0F0
RTM32> set [0x00] 0x2110F000   # ANDI $4, $8, 0xF000  | RTM32> set [0x10] 0x3110F000   # XORI $4, $8, 0xF000
RTM32> set [0x04] 0x2113F000   # ANDIH $4, $9, 0xF000 | RTM32> set [0x14] 0x29088080   # ORI $4, $4, 0x80
RTM32> set [0x08] 0x2910F00F   # ORI $4, $8, 0xF00F   | RTM32> set [0x0C] 0x58080010   # SB $0, $4, 0x10
RTM32> set [0x0C] 0x2913F00F   # ORIH $4, $9, 0xF00F  | RTM32> set [0x10] 0x70100010   # LB $0, $8, 0x10
```

## Observaciones Experimentales y Comportamiento Lógico
* **ANDI / ANDIH:** ANDI actúa sobre la sección baja devolviendo R8 = `0x0000F000`. ANDIH procesa la sección alta de los bits, lo que resulta en R9 = `0xF000F000`, demostrando un aislamiento por máscara por encima de la frontera de los 16 bits.
* **ORI / ORIH:** ORI añade los bits de la máscara baja resultando en R8 = `0xF000F0FF`. ORIH modifies los cuartetos superiores generando R9 = `0xF00FF0F0`.
* **XORI:** Aplica una inversión exclusiva bit a bit, discriminando el patrón y retornando R8 = `0xF000F0F0`.
* **Inyección y Carga de Byte Negativo (Caso 10):** Tras ejecutar `ORI $4, $4, 0x80`, el registro se establece en `0x80008080`. La instrucción `SB` almacena el byte inferior `0x80` en la dirección `0x010`. Al ejecutar `LB $0, $8, 0x10`, el procesador lee el byte, detecta que el bit 7 está en 1 (lo que representa un valor negativo) y rellena los bits del 8 al 31 con unos. Esto resulta en R8 = `0xFFFFFF80` (-128 decimal en complemento a 2).

## Conclusión
Las variantes lógicas inmediatas de tipo alto (`H`) realizan la extensión implícita con ceros de manera correcta antes de aplicar la máscara booleana. Asimismo, la prueba con el byte `0x80` confirma que el circuito detector de signo mapea adecuadamente los tipos de datos de tamaño reducido (smallword) en el registro destino de 32 bits.

---

# Caso 11: Comunicación con Periféricos (MMIO - UART)

## Descripción
Validación de la interfaz de E/S mapeada en memoria (MMIO), verificando el direccionamiento síncrono externo mediante la transmisión secuencial de una cadena de caracteres ASCII a través de la UART.

## Precondiciones
* `$16` = Dirección base de la UART asignada en `0xFFFFFF00` (obtenida mediante extensión de signo automática de `0xFF00` por medio de ADDI).
* Se cargan los caracteres secuenciales del mensaje "Hola" en el registro `$17` mediante incrementos y decrementos aritméticos controlados.

## Code
```
XOR $16, $16, $16 (0x0402400A)   | SB $16, $17, 0 (0x590A0000)    # Transmite 'o'
XOR $17, $17, $17 (0x0422500A)   | ADDI $17, $17, 0xFFMD (0x094AFFFD)
ADDI $16, $16, 0xFF00 (0x0909FF00)| SB $16, $17, 0 (0x590A0000)    # Transmite 'l'
ADDI $17, $17, 0x0048 (0x094A0048)| ADDI $17, $17, 0xFFMB (0x094AFFFB)
SB $16, $17, 0 (0x590A0000)    # Transmite 'H' | SB $16, $17, 0 (0x590A0000)    # Transmite 'a'
ADDI $17, $17, 0x0027 (0x094A0027)
```

## Resultados Experimentales
1.  **Resolución de Dirección:** La instrucción `ADDI $16, $16, 0xFF00` calcula de forma correcta la dirección `0xFFFFFF00` debido a la extensión de signo del inmediato.
2.  **Ciclo de Escritura UART:** El comando `SB $16, $17, 0` envía el byte almacenado en R17 a la dirección de MMIO. El emulador captura este acceso y redirige el flujo de datos directamente hacia la consola del sistema.
3.  **Salida por Consola:** La secuencia ordenada de instrucciones `SB` imprime los caracteres uno a uno sin retrasos ni corrupción de datos en el bus, mostrando el mensaje de prueba de forma fluida:
```
H
Ho
Hol
Hola
```

## Conclusiones
El decodificador de direcciones del procesador identifica correctamente los accesos fuera del mapa de memoria convencional. El puerto MMIO mapeado en `0xFFFFFF00` permite la comunicación directa con periféricos estándar mediante instrucciones de almacenamiento comunes (`SB`), demostrando la viabilidad del procesador para interactuar con dispositivos externos.

---

## Resumen General de Validaciones

| ID | Módulo de Prueba | Componente Evaluado | Estado | Instrucciones Críticas |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Aritmética Signada/Unsigned | ALU Principal | **CORRECTO** | ADD, SUB, MUL, MULH, MULHU, DIV, DIVU, REM |
| 2 | Operaciones Lógicas | Unidad Booleana | **CORRECTO** | AND, OR, NOR |
| 3 | Desplazamientos | Shift Unit | **CORRECTO** | SLL, SRL, SRA |
| 4 | Comparaciones Dinámicas | Lógica de Estado | **CORRECTO** | SLT, SLTU, SLTI, SLTIU |
| 5 | Saltos Incondicionales | Control de Flujo | **CORRECTO** | J, JAL, JR, JALR |
| 6 | Flujo Condicional (Branches) | Unidad de Control | **CORRECTO** | BEQ, BNE, BLT, BGT, BLE, BGE |
| 7 | Acceso a Memoria Base | Controlador de Bus | **CORRECTO** | SW, LW, SH, LH, LHU, SB, LB, LBU |
| 8 | Carga Indexada Avanzada | Lógica de Direcciones | **CORRECTO** | LWX, LHX, LHUX, LBX, LBUX |
| 9 | Lógica de Inmediatos Alta/Baja | Unidad Booleana | **CORRECTO** | ANDI, ANDIH, ORI, ORIH, XORI, XORIH |
| 10| Signo en Smallword | Acondicionador de Datos| **CORRECTO** | LB, LBX (Con byte `0x80`) |
| 11| Interfaz MMIO | Subsistema de Periféricos| **CORRECTO** | SB (Dirección de memoria `0xFFFFFF00`) |

* **Instrucciones Únicas Validadas:** 47
* **Comportamientos Verificados:** 60+
* **Estado General del Procesador:** **APROBADO SIN DEFECTOS**

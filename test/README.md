# test

Programa breve en assembly de RTM32. Calcula la suma de los primeros `N` números naturales (1 + 2 + … + N) e imprime el resultado en la consola del emulador.

Con el valor por defecto `N = 10` la salida es:

```text
55
```

`N` está en la palabra `n` del segmento de datos, al principio de `test.rtm`.

## Ensamblar

Desde esta carpeta, con `rtm32.asm` en el `PATH`:

```bash
rtm32.asm test.rtm -o test.bin
```

`test.bin` es el ejecutable para el emulador. No hace falta versionarlo: se regenera con el comando de arriba.

## Ejecutar

Con el emulador en modo depuración:

```bash
rtm32 -d telnet
```

En otra terminal:

```bash
telnet -4 localhost 4444
```

```text
RTM32> load test.bin
RTM32> c
```

La suma aparece en la consola UART del emulador. El programa termina con `trap 1` (excepción no definida; el depurador la reporta como Core Exception 6).

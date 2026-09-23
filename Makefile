ASM ?= rtm32.asm
SRC = test.rtm
OUT = test.bin

.PHONY: all clean

all: $(OUT)

$(OUT): $(SRC)
	$(ASM) $(SRC) -o $(OUT)

clean:
	rm -f $(OUT)

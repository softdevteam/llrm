CLANG_CC = clang

CFLAGS := -g $(shell llvm-config --cflags) -std=c99
LDFLAGS := $(shell llvm-config --cxxflags --ldflags --libs core native --system-libs) -lclang

.PHONY: all clean

all: test.bc

test.bc: test.c
	$(CLANG_CC) -emit-llvm test.c -c -O2  -o test.bc

clean:
	-rm -f test.bc test test.o test.ll test.s

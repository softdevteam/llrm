CLANG_CC = clang

CFLAGS := -g $(shell llvm-config --cflags) -std=c99
LDFLAGS := $(shell llvm-config --cxxflags --ldflags --libs core native --system-libs) -lclang

.PHONY: all clean

all: test.bc llvmtest

test.bc: test.c
	$(CLANG_CC) -emit-llvm test.c -c -o test.bc

llvmtest: llvmtest.o
	$(CC) $< $(LDFLAGS) -o $@

clean:
	-rm -f llvmtest.o llvmtest test.bc test test.o test.ll test.s

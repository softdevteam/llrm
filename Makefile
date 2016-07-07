CLANG_CC = clang

CFLAGS := -g $(shell llvm-config --cflags) -std=c99
LDFLAGS := $(shell llvm-config --cxxflags --ldflags --libs core native --system-libs) -lclang

.PHONY: all clean

all: test.bc fibonacci_rec.bc fibonacci_iter.bc

test.bc: test.c
	$(CLANG_CC) -emit-llvm test.c -c -O2  -o test.bc

fibonacci_iter.bc: fibonacci_iter.c
	$(CLANG_CC) -emit-llvm fibonacci_iter.c -c -O2  -o fibonacci_iter.bc

fibonacci_rec.bc: fibonacci_rec.c
	$(CLANG_CC) -emit-llvm fibonacci_rec.c -c -O2  -o fibonacci_rec.bc

interpreter-c: interpreter.py
	$(PYTHONPATH) -O0 interpreter.py

benchmark: interpreter-c fibonacci_rec.bc fibonacci_iter.bc
	./multitime -n5 -q ./interpreter-c fibonacci_rec.bc
	./multitime -n5 -q ./interpreter-c fibonacci_iter.bc
clean:
	-rm -f *.bc *.o *.ll *.s test fibonacci_rec fibonacci_iter

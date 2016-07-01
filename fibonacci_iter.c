#include <stdio.h>

int fibonacci_iter(int n)
{
    int last = 0, old_current = 0, current = 1;
    while(n) {
        old_current = current;
        current += last;
        last = old_current;
        --n;
    }
    return current;
}

int main(int argc, char *argv[])
{
    printf("%d", fibonacci_iter(10));
    return 0;
}

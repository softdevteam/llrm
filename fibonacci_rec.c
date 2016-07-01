#include <stdio.h>

int fibonacci_rec(int n)
{
    if(n < 2) {
        return 1;
    }
    else {
        return fibonacci_rec(n - 1) + fibonacci_rec(n - 2);
    }
}

int main(int argc, char *argv[])
{
    printf("%d", fibonacci_rec(10));
    return 0;
}

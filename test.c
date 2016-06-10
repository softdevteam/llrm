#include <stdio.h>

int
abs_test(int a, int b)
{
    if( a > b ) {
        return a - b;
    }
    return b - a;
}

int
main(int argc, char *argv[])
{
    int a = 20;
    int b = 13;

    printf("%d\n", abs_test(a, b));

    return 0;
}

#include <stdio.h>

int
main(int argc, char *argv[])
{
    int a = 20;
    int b = 13;
    int something = 100;
    int c = a + b + something;

    printf("c is %d and argc is %d and argc + 1 is %d\n", c, argc, argc +1);
    printf("argc is %d\n", argc);
    printf("5 * argc + 1 is %d\n", 5 * argc + 1);

    return 0;
}

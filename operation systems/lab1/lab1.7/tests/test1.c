#include "uthread.h"
#include <stdio.h>
#include <unistd.h>
#include <string.h>

void *thread_func(void *arg) {
    char *str = (char *)arg;
    for (int i = 0; i < 3; ++i) {
        printf("Thread: %s (%d)\n", str, i);
        sleep(1);
        uthread_scheduler();
    }
    return str;
}

int main() {
    uthread_t thread;
    void *retval;
    printf("Test1: Initializing library...\n");
    if (uthread_init() == -1) {
        printf("Test1: Initialization failed\n");
        return 1;
    }
    printf("Test1: Creating one thread...\n");
    if (uthread_create(&thread, thread_func, "Hello") == -1) {
        printf("Test1: Create failed\n");
        return 1;
    }
    if (uthread_join(thread, &retval) == -1) {
        printf("Test1: Join failed\n");
        return 1;
    }
    if (strcmp((char *)retval, "Hello") == 0) {
        printf("Test1: Thread returned correct value\n");
    } else {
        printf("Test1: Wrong retval\n");
        return 1;
    }
    printf("Test1: Passed\n");
    uthread_cleanup();
    return 0;
}

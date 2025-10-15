#include "mythread.h"
#include <stdio.h>
#include <unistd.h>
#include <string.h>

void *thread_func(void *arg) {
    char *str = (char *)arg;
    for (int i = 0; i < 3; ++i) {
        printf("Thread: %s (%d)\n", str, i);
        sleep(1);
    }
    return "Thread done";
}

int main() {
    mythread_t thread;
    void *retval;
    printf("Test1: Creating one thread...\n");
    if (mythread_create(&thread, thread_func, "Hello") == -1) {
        printf("Test1: Create failed\n");
        return 1;
    }
    if (mythread_join(thread, &retval) == -1) {
        printf("Test1: Join failed\n");
        return 1;
    }
    if (strcmp((char *)retval, "Thread done") == 0) {
        printf("Test1: Thread returned correct value\n");
    } else {
        printf("Test1: Wrong retval\n");
        return 1;
    }
    printf("Test1: Passed\n");
    return 0;
}

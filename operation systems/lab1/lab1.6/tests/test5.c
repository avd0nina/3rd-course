#include "mythread.h"
#include <stdio.h>
#include <unistd.h>
#include <string.h>

void *thread_func(void *arg) {
    char *str = (char *)arg;
    for (int i = 0; i < 2; ++i) {
        printf("Thread: %s (%d)\n", str, i);
        sleep(2);
    }
    return str;
}

int main() {
    mythread_t threads[2];
    char *args[2] = {"Thread A", "Thread B"};
    void *retval;
    printf("Test5: Creating 2 threads with different args...\n");
    for (int i = 0; i < 2; ++i) {
        if (mythread_create(&threads[i], thread_func, args[i]) == -1) {
            printf("Test5: Create failed\n");
            return 1;
        }
    }
    for (int i = 1; i >= 0; --i) {
        if (mythread_join(threads[i], &retval) == -1) {
            printf("Test5: Join failed\n");
            return 1;
        }
        printf("Test5: Joined %s\n", (char *)retval);
    }
    printf("Test5: Passed\n");
    return 0;
}

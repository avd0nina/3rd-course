#include "uthread.h"
#include <stdio.h>
#include <unistd.h>

int shared_counter = 0;

void *thread_func(void *arg) {
    (void)arg;
    for (int i = 0; i < 100; ++i) {
        shared_counter++;
        usleep(1000);
        uthread_scheduler();
    }
    return NULL;
}

int main() {
    uthread_t threads[2];
    int args[2] = {1, 2};
    void *retval;
    printf("Test5: Initializing library...\n");
    if (uthread_init() == -1) {
        printf("Test5: Initialization failed\n");
        return 1;
    }
    printf("Test5: 2 threads incrementing shared counter...\n");
    for (int i = 0; i < 2; ++i) {
        if (uthread_create(&threads[i], thread_func, &args[i]) == -1) {
            printf("Test5: Create failed\n");
            return 1;
        }
    }
    for (int i = 0; i < 2; ++i) {
        if (uthread_join(threads[i], &retval) == -1) {
            printf("Test5: Join failed\n");
            return 1;
        }
    }
    printf("Test5: Shared counter: %d\n", shared_counter);
    if (shared_counter > 150) {
        printf("Test5: Passed\n");
    } else {
        printf("Test5: Failed\n");
        return 1;
    }
    uthread_cleanup();
    return 0;
}

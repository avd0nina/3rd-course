#include "uthread.h"
#include <stdio.h>
#include <unistd.h>

void *thread_func(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < 4; ++i) {
        printf("Thread %d: iteration %d\n", id, i);
        sleep(1);
        uthread_scheduler();
    }
    return NULL;
}

int main() {
    uthread_t threads[3];
    int args[3] = {1, 2, 3};
    void *retval;
    printf("Test2: Initializing library...\n");
    if (uthread_init() == -1) {
        printf("Test2: Initialization failed\n");
        return 1;
    }
    printf("Test2: Creating 3 threads...\n");
    for (int i = 0; i < 3; ++i) {
        if (uthread_create(&threads[i], thread_func, &args[i]) == -1) {
            printf("Test2: Create failed for thread %d\n", i);
            return 1;
        }
    }
    for (int i = 0; i < 3; ++i) {
        if (uthread_join(threads[i], &retval) == -1) {
            printf("Test2: Join failed for thread %d\n", i);
            return 1;
        }
    }
    printf("Test2: All threads joined\n");
    printf("Test2: Passed\n");
    uthread_cleanup();
    return 0;
}

#include "uthread.h"
#include <stdio.h>
#include <unistd.h>

void *thread_func(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < 2; ++i) {
        printf("Thread %d: iteration %d\n", id, i);
        sleep(1);
        uthread_scheduler();
    }
    return NULL;
}

int main() {
    uthread_t threads[MAX_THREADS_COUNT];
    int args[MAX_THREADS_COUNT];
    void *retval;
    printf("Test4: Initializing library...\n");
    if (uthread_init() == -1) {
        printf("Test4: Initialization failed\n");
        return 1;
    }
    printf("Test4: Creating %d threads...\n", MAX_THREADS_COUNT);
    for (int i = 0; i < MAX_THREADS_COUNT; ++i) {
        args[i] = i + 1;
        if (uthread_create(&threads[i], thread_func, &args[i]) == -1) {
            if (i == MAX_THREADS_COUNT - 1) {
                printf("Test4: Create failed as expected (max threads)\n");
                break;
            } else {
                printf("Test4: Create failed unexpectedly for thread %d\n", i);
                return 1;
            }
        }
    }
    for (int i = 0; i < MAX_THREADS_COUNT - 1; ++i) {
        if (uthread_join(threads[i], &retval) == -1) {
            printf("Test4: Join failed for thread %d\n", i);
            return 1;
        }
    }
    printf("Test4: Passed\n");
    uthread_cleanup();
    return 0;
}

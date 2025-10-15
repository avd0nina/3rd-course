#include "mythread.h"
#include <stdio.h>
#include <unistd.h>

#define NUM_THREADS 1000

void *thread_func(void *arg) {
   // int id = *(int *)arg;
    (void)arg;
    for (int i = 0; i < 4; ++i) {
        // printf("Thread %d: iteration %d\n", id, i);
        sleep(1);
    }
    return NULL;
}

int main() {
    mythread_t threads[NUM_THREADS];
    int args[NUM_THREADS];
    void *retval;
    printf("Test2.1: Creating %d threads...\n", NUM_THREADS);
    for (int i = 0; i < NUM_THREADS; ++i) {
        args[i] = i + 1; 
        if (mythread_create(&threads[i], thread_func, &args[i]) == -1) {
            printf("Test2.1: Create failed for thread %d\n", i);
            return 1;
        }
    }
    for (int i = 0; i < NUM_THREADS; ++i) {
        if (mythread_join(threads[i], &retval) == -1) {
            printf("Test2.1: Join failed for thread %d\n", i);
            return 1;
        }
    }
    printf("Test2.1: All threads joined\n");
    printf("Test2.1: Passed\n");
    return 0;
}

#include "mythread.h"
#include <stdio.h>
#include <unistd.h>
#include <stdatomic.h>

atomic_int shared_counter = 0;

void *thread_func(void *arg) {
    (void)arg;
    printf("Thread started\n");
    for (int i = 0; i < 10; ++i) {
        atomic_fetch_add(&shared_counter, 1);
        usleep(10000);
        printf("Thread: counter = %d\n", atomic_load(&shared_counter));
    }
    printf("Thread finished\n");
    return NULL;
}

int main() {
    mythread_t threads[2];
    void *retval;
    printf("Test4: Starting...\n");
    for (int i = 0; i < 2; ++i) {
        printf("Creating thread %d\n", i);
        if (mythread_create(&threads[i], thread_func, NULL) == -1) {
            printf("Test4: Create failed for thread %d\n", i);
            return 1;
        }
    }
    printf("All threads created, waiting for completion...\n");
    for (int i = 0; i < 2; ++i) {
        if (mythread_join(threads[i], &retval) == -1) {
            printf("Test4: Join failed for thread %d\n", i);
            return 1;
        }
        printf("Thread %d joined\n", i);
    }
    int result = atomic_load(&shared_counter);
    printf("Test4: Final counter value: %d\n", result);
    if (result == 20) {
        printf("Test4: Passed\n");
        return 0;
    }
    return 1; 
}

#include "mythread.h"
#include <stdio.h>
#include <unistd.h>

void *thread_func(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < 4; ++i) {
        // printf("Thread %d: iteration %d\n", id, i);
        sleep(1);
    }
    return NULL;
}

int main() {
    int num_threads;
    printf("Enter number of threads: ");
    if (scanf("%d", &num_threads) != 1 || num_threads <= 0) {
        printf("Invalid input. Please enter a positive integer.\n");
        return 1;
    }
    mythread_t threads[num_threads];
    int args[num_threads];
    void *retval;
    printf("Test2.2: Creating %d threads...\n", num_threads);
    for (int i = 0; i < num_threads; ++i) {
        args[i] = i + 1;
        if (mythread_create(&threads[i], thread_func, &args[i]) == -1) {
            printf("Test2.2: Create failed for thread %d\n", i);
            return 1;
        }
    }
    for (int i = 0; i < num_threads; ++i) {
        if (mythread_join(threads[i], &retval) == -1) {
            printf("Test2.2: Join failed for thread %d\n", i);
            return 1;
        }
    }
    printf("Test2.2: All threads joined\n");
    printf("Test2.2: Passed\n");
    return 0;
}

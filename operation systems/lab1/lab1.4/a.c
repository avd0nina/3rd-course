#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>  // for sleep

void* thread_func(void* arg) {
    while (1) {
        printf("Thread printing...\n");
        fflush(stdout);
    }
    return NULL;
}

int main() {
    pthread_t thread;
    if (pthread_create(&thread, NULL, thread_func, NULL) != 0) {
        perror("pthread_create");
        exit(1);
    }

    sleep(3);
    if (pthread_cancel(thread) != 0) {
        perror("pthread_cancel");
    }

    void* retval;
    if (pthread_join(thread, &retval) != 0) {
        perror("pthread_join");
    }
    printf("Thread cancelled, retval: %p\n", retval);
    return 0;
}

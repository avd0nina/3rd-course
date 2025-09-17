#include <stdio.h>
#include <stdlib.h>
#include <string.h>  // for strcpy
#include <pthread.h>
#include <unistd.h>

void cleanup_handler(void* arg) {
    free(arg);
    printf("Memory is cleaned\n");
}

void* thread_func(void* arg) {
    char* str = malloc(12);
    if (!str) {
        perror("malloc");
        return NULL;
    }
    strcpy(str, "hello world");
    pthread_cleanup_push(cleanup_handler, str);
    while (1) {
        printf("%s\n", str);
        fflush(stdout);
    }
    pthread_cleanup_pop(1);
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
    printf("Thread cancelled\n");
    return 0;
}

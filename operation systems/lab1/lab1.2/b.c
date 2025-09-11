#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

void *mythread(void *arg) {
    printf("mythread [%d %d %d]: Hello from mythread!\n", getpid(), getppid(), gettid());
    int *val = malloc(sizeof(int)); // выделяем память именно на куче, т.к. после завершения потока его стек разрушится
    if (val == NULL) {
        fprintf(stderr, "mythread: malloc failed\n");
        return NULL;
    }
    *val = 42;
    return (void *)val;
}

int main() {
    pthread_t tid;
    int err;
    printf("main [%d %d %d]: Hello from main!\n", getpid(), getppid(), gettid());
    err = pthread_create(&tid, NULL, mythread, NULL);
    if (err) {
        printf("main: pthread_create() failed: %s\n", strerror(err));
        return -1;
    }
    printf("in main create new thread with tid %ld\n", tid);
    void *thread_result;
    err = pthread_join(tid, &thread_result);
    if (err) {
        printf("main: pthread_join() failed: %s\n", strerror(err));
        return -1;
    }
    if (thread_result == NULL) {
        printf("main: thread returned NULL\n");
        return -1;
    }
    printf("Thread returned: %d\n", *(int *)thread_result);
    free(thread_result);

    return 0;
}

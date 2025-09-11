#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/syscall.h>

typedef struct {
    int param1;
    char *param2;
} thread_args;

void *mythread(void *arg) {
    thread_args *input_args = (thread_args *)arg;
    printf("mythread tid = %ld, params: %d, %s\n", gettid(), input_args->param1, input_args->param2);
    return NULL;
}

int main() {
    pthread_t tid;
    int err;
    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), gettid());
    thread_args args;
    args.param1 = 42;
    args.param2 = "hello world";
    err = pthread_create(&tid, NULL, mythread, &args);
    if (err) {
        printf("main: pthread_create() failed: %s\n", strerror(err));
        return -1;
    }
    printf("main: created thread with tid %ld\n", tid);
    err = pthread_join(tid, NULL);
    if (err) {
        printf("main: pthread_join() failed: %s\n", strerror(err));
        return -1;
    }
    return 0;
}

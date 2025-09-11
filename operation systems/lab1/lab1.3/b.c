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
    free(input_args); // освобождаем память в куче самостоятельно, т.к. основной поток может закончитьсмя раньше доченего
    return NULL;
}

int main() {
    pthread_t tid;
    int err;
    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), gettid());
    thread_args *args = malloc(sizeof(thread_args)); // структура выделяется в куче, потому что основной поток может закончиться раньше, чем дочерние, и стек разрушится. а куча - это общая память, доступная для всех потоков, пока не будет вызван free
    if (args == NULL) {
        printf("main: malloc failed\n");
        return -1;
    }
    args->param1 = 42;
    args->param2 = "hello world";
    err = pthread_create(&tid, NULL, mythread, args);
    if (err) {
        printf("main: pthread_create() failed: %s\n", strerror(err));
        free(args);
        return -1;
    }
    printf("main: created thread with tid %ld\n", tid);
    pthread_detach(tid); // делаем поток detached
    pthread_exit(NULL); // завершаем основной поток
    return 0; 
}

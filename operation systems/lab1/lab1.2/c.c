#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

void *mythread(void *arg) {
    printf("mythread [%d %d %d]: Hello from mythread!\n", getpid(), getppid(), gettid());
    char *str = malloc(sizeof(char) * 12); // выделяем память на куче
    if (str == NULL) {
        fprintf(stderr, "mythread: malloc failed\n");
        return NULL;
    }
    strcpy(str, "hello world");
    return (void *)str;
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
    printf("Thread returned: %s\n", (char *)thread_result);
    free(thread_result);

    return 0;
}

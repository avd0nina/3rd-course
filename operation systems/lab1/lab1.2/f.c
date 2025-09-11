#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>

void *mythread(void *arg) {
    printf("mythread tid = %ld\n", pthread_self());
    return NULL;
}

int main() {
    pthread_t tid;
    int err;
    pthread_attr_t attr;
    err = pthread_attr_init(&attr);
    if (err) {
        printf("main: pthread_attr_init() failed: %s\n", strerror(err));
        return -1;
    }
    err = pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
    if (err) {
        printf("main: pthread_attr_setdetachstate() failed: %s\n", strerror(err));
        return -1;
    }
    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), syscall(SYS_gettid));
    while (1) {
        err = pthread_create(&tid, &attr, mythread, NULL);
        if (err) {
            printf("main: pthread_create() failed: %s\n", strerror(err));
            return -1;
        }
    }
    pthread_attr_destroy(&attr);
    return 0;
}

// main: pthread_create() failed: Resource temporarily unavailable

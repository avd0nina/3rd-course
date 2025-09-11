#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>

void *mythread(void *arg) {
    printf("mythread tid = %ld\n", pthread_self());
    pthread_detach(pthread_self());
    return NULL;
}

int main() {
    pthread_t tid;
    int err;

    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), syscall(SYS_gettid));

    while (1) {
        err = pthread_create(&tid, NULL, mythread, NULL);
        if (err) {
            printf("main: pthread_create() failed: %s\n", strerror(err));
            return -1;
        }
    }
    return 0;
}

// main: pthread_create() failed: Resource temporarily unavailable

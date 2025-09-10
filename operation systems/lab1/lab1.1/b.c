#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/syscall.h>

void *mythread(void *arg) {
    printf("mythread [%d %d %ld]: Hello from mythread!\n", getpid(), getppid(), gettid());
    return NULL;
}

int main() {
    pthread_t tid[5];
    int err;
    int i;

    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), gettid());

    for (i = 0; i < 5; i++) {
        err = pthread_create(&tid[i], NULL, mythread, NULL);
        if (err) {
            printf("main: pthread_create() failed for thread %d: %s\n", i, strerror(err));
            return -1;
        }
    }

    for (i = 0; i < 5; i++) {
        err = pthread_join(tid[i], NULL);
        if (err) {
            printf("main: pthread_join() failed for thread %d: %s\n", i, strerror(err));
            return -1;
        }
    }
    return 0;
}

#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>

void sigint_handler(int signo) {
    printf("Thread 2 received SIGINT (%d)\n", signo);
}

void *thread_func_1() {
    sigset_t mask;
    sigfillset(&mask);
    if (pthread_sigmask(SIG_BLOCK, &mask, NULL) != 0) { // блокируем все сигналы
        perror("pthread_sigmask in thread 1\n");
        return NULL;
    }
    for (int i = 0; i < 3; i++) {
        pthread_kill(pthread_self(), SIGSEGV); // посылаем сегфолт самому себе для теста
        printf("Thread 1 blocked all signals\n");
    }
    return NULL;
}

void *thread_func_2() {
    signal(SIGINT, sigint_handler);
    printf("Thread 2: Waiting for SIGINT (Ctrl+C)\n");
}

void *thread_func_3() {
    sigset_t mask;
    int signo;
    sigemptyset(&mask);
    sigaddset(&mask, SIGQUIT);
    if (pthread_sigmask(SIG_BLOCK, &mask, NULL) != 0) {
        perror("pthread_sigmask in thread 3\n");
        return NULL;
    }
    printf("Thread 3: Waiting for SIGQUIT (Ctrl+\\)\n");
    while (1) {
        int err = sigwait(&mask, &signo);
        if (err != 0) {
            perror("sigwait");
            return NULL;
        }
        if (signo == SIGQUIT) {
            printf("Thread 3 received SIGQUIT\n");
        }
    }
    return NULL;
}

int main() {
    pthread_t tid_1, tid_2, tid_3;
    int err;
    printf("main [%d %d %d]: Hello from main!\n", getpid(), getppid(), gettid());
    err = pthread_create(&tid_1, NULL, thread_func_1, NULL);
    if (err) {
        fprintf(stderr, "Main: pthread_create thread1 failed: %s\n", strerror(err));
        return -1;
    }
    err = pthread_create(&tid_2, NULL, thread_func_2, NULL);
    if (err) {
        fprintf(stderr, "Main: pthread_create thread2 failed: %s\n", strerror(err));
        return -1;
    }
    err = pthread_create(&tid_3, NULL, thread_func_3, NULL);
    if (err) {
        fprintf(stderr, "Main: pthread_create thread3 failed: %s\n", strerror(err));
        return -1;
    }
    pthread_join(tid_1, NULL);
    pthread_join(tid_2, NULL);

    printf("Main: Sending SIGQUIT to thread3...\n");
    pthread_kill(tid_3, SIGQUIT);
    pthread_kill(tid_3, SIGQUIT);

    pthread_join(tid_3, NULL);
    return 0;
}

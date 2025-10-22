#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <unistd.h>
#include <sched.h>
#include "queue.h"

#define RED "\033[41m"
#define NOCOLOR "\033[0m"

void set_cpu(int n) {
    int err;
    cpu_set_t cpuset;
    pthread_t tid = pthread_self();
    CPU_ZERO(&cpuset);
    CPU_SET(n, &cpuset);
    err = pthread_setaffinity_np(tid, sizeof(cpu_set_t), &cpuset);
    if (err) {
        printf("set_cpu: pthread_setaffinity failed for cpu %d\n", n);
        return;
    }
    printf("set_cpu: set cpu %d\n", n);
}

typedef struct {
    queue_t *q;
    int cpu_id;
} thread_args_t;

void *reader(void *arg) {
    thread_args_t *args = (thread_args_t *)arg;
    int expected = 0;
    queue_t *q = args->q;
    int reader_cpu = args->cpu_id;
    printf("reader [%d %d %d] CPU: %d\n", getpid(), getppid(), gettid(), reader_cpu);
    set_cpu(reader_cpu);
    while (1) {
        int val = -1;
        int ok = queue_get(q, &val);
        if (!ok)
            continue;
        if (expected != val)
            printf(RED"ERROR: get value is %d but expected - %d" NOCOLOR "\n", val, expected);
        expected = val + 1;
    }
    return NULL;
}

void *writer(void *arg) {
    thread_args_t *args = (thread_args_t *)arg;
    int i = 0;
    queue_t *q = args->q;
    int writer_cpu = args->cpu_id;
    printf("writer [%d %d %d] CPU: %d\n", getpid(), getppid(), gettid(), writer_cpu);
    set_cpu(writer_cpu);
    while (1) {
        int ok = queue_add(q, i);
        if (!ok)
            continue;
        i++;
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    pthread_t tid[2];
    queue_t *q;
    int err;
    int reader_cpu = 1;
    int writer_cpu = 1;
    if (argc > 2) {
        reader_cpu = atoi(argv[1]);
        writer_cpu = atoi(argv[2]);
    }
    printf("main [%d %d %d] Reader CPU: %d, Writer CPU: %d\n",
           getpid(), getppid(), gettid(), reader_cpu, writer_cpu);
    q = queue_init(1000000);
    thread_args_t reader_args = {q, reader_cpu};
    thread_args_t writer_args = {q, writer_cpu};
    err = pthread_create(&tid[0], NULL, reader, &reader_args);
    if (err) {
        printf("main: pthread_create() failed: %s\n", strerror(err));
        return -1;
    }
    sched_yield();
    err = pthread_create(&tid[1], NULL, writer, &writer_args);
    if (err) {
        printf("main: pthread_create() failed: %s\n", strerror(err));
        return -1;
    }
    printf("main: waiting for threads to complete...\n");
    pthread_join(tid[0], NULL);
    pthread_join(tid[1], NULL);
    return 0;
}

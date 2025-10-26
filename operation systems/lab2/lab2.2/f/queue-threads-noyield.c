#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <unistd.h>
#include <sched.h>
#include <sys/time.h>
#include <sys/resource.h>
#include "queue.h"

#define RED "\033[41m"
#define NOCOLOR "\033[0m"
#define RUN_TIME 5

volatile int running = 1;

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
}

void *reader(void *arg) {
    int expected = 0;
    queue_t *q = (queue_t *)arg;
    set_cpu(1);
    while (running) {
        int val = -1;
        int ok = queue_get(q, &val);
        if (!ok) continue;
        if (expected != val)
            printf(RED"ERROR: get value is %d but expected - %d" NOCOLOR "\n", val, expected);
        expected = val + 1;
    }
    return NULL;
}

void *writer(void *arg) {
    int i = 0;
    queue_t *q = (queue_t *)arg;
    set_cpu(1);
    while (running) {
        int ok = queue_add(q, i);
        if (!ok) continue;
        i++;
    }
    return NULL;
}

void *timer_thread(void *arg) {
    sleep(RUN_TIME);
    running = 0;
    return NULL;
}

int main() {
    pthread_t tid[3];
    queue_t *q;
    int err;
    
    printf("Testing with CONDITION VARIABLES and no sched_yield\n");
    
    struct rusage start_usage, end_usage;
    getrusage(RUSAGE_SELF, &start_usage);
    
    q = queue_init(1000000);
    
    long start_add_attempts = q->add_attempts;
    long start_get_attempts = q->get_attempts;
    long start_add_count = q->add_count;
    long start_get_count = q->get_count;
    
    err = pthread_create(&tid[2], NULL, timer_thread, NULL);
    if (err) {
        printf("pthread_create(timer) failed: %s\n", strerror(err));
        return -1;
    }
    
    err = pthread_create(&tid[0], NULL, reader, q);
    if (err) {
        printf("pthread_create(reader) failed: %s\n", strerror(err));
        return -1;
    }

    err = pthread_create(&tid[1], NULL, writer, q);
    if (err) {
        printf("pthread_create(writer) failed: %s\n", strerror(err));
        return -1;
    }
    
    pthread_join(tid[2], NULL);
    running = 0;
    
    pthread_cond_broadcast(&q->not_empty);
    pthread_cond_broadcast(&q->not_full);
    
    pthread_join(tid[0], NULL);
    pthread_join(tid[1], NULL);
    
    getrusage(RUSAGE_SELF, &end_usage);
    
    double user_time = (end_usage.ru_utime.tv_sec - start_usage.ru_utime.tv_sec) +
                      (end_usage.ru_utime.tv_usec - start_usage.ru_utime.tv_usec) / 1000000.0;
    double system_time = (end_usage.ru_stime.tv_sec - start_usage.ru_stime.tv_sec) +
                        (end_usage.ru_stime.tv_usec - start_usage.ru_stime.tv_usec) / 1000000.0;
    
    long total_add_attempts = q->add_attempts - start_add_attempts;
    long total_get_attempts = q->get_attempts - start_get_attempts;
    long total_add_count = q->add_count - start_add_count;
    long total_get_count = q->get_count - start_get_count;
    
    printf("\n=== RESULTS WITH CONDITION VARIABLES (No sched_yield) ===\n");
    printf("CPU Time: user=%.3fs, system=%.3fs, total=%.3fs\n",
           user_time, system_time, user_time + system_time);
    printf("Operations: add_attempts=%ld, get_attempts=%ld\n",
           total_add_attempts, total_get_attempts);
    printf("Successful: adds=%ld, gets=%ld\n", total_add_count, total_get_count);
    printf("Queue: current_size=%d, utilization=%.1f%%\n",
           q->count, q->count * 100.0 / q->max_count);
    
    queue_destroy(q);
    return 0;
}

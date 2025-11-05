#include "queue.h"
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define STORAGE_CAPACITY 1000
#define THREAD_COUNT 6
#define ASC 0
#define DESC 1
#define EQ 2
#define SWAP1 3
#define SWAP2 4
#define SWAP3 5

volatile sig_atomic_t running = 1;

Storage *global_storage = NULL;

void handle_sigint(int sig) {
    (void)sig;
    running = 0;
}

void *ascending_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        custom_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        custom_mutex_unlock(&storage->head_mutex);
        if (!curr) { usleep(1000); continue; }
        custom_mutex_lock(&curr->sync);
        Node *next = curr->next;
        while (next && running) {
            custom_mutex_lock(&next->sync);
            if (strlen(curr->value) < strlen(next->value)) local_count++;
            custom_mutex_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        if (curr) custom_mutex_unlock(&curr->sync);
        custom_mutex_lock(&global_mutex);
        asc_pairs = local_count;
        (*counter)++;
        custom_mutex_unlock(&global_mutex);
        usleep(1000);
    }
    return NULL;
}

void *descending_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        custom_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        custom_mutex_unlock(&storage->head_mutex);
        if (!curr) { usleep(1000); continue; }
        custom_mutex_lock(&curr->sync);
        Node *next = curr->next;
        while (next && running) {
            custom_mutex_lock(&next->sync);
            if (strlen(curr->value) > strlen(next->value)) local_count++;
            custom_mutex_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        if (curr) custom_mutex_unlock(&curr->sync);
        custom_mutex_lock(&global_mutex);
        desc_pairs = local_count;
        (*counter)++;
        custom_mutex_unlock(&global_mutex);
        usleep(1000);
    }
    return NULL;
}

void *equal_length_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        custom_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        custom_mutex_unlock(&storage->head_mutex);
        if (!curr) { usleep(1000); continue; }
        custom_mutex_lock(&curr->sync);
        Node *next = curr->next;
        while (next && running) {
            custom_mutex_lock(&next->sync);
            if (strlen(curr->value) == strlen(next->value)) local_count++;
            custom_mutex_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        if (curr) custom_mutex_unlock(&curr->sync);
        custom_mutex_lock(&global_mutex);
        eq_pairs = local_count;
        (*counter)++;
        custom_mutex_unlock(&global_mutex);
        usleep(1000);
    }
    return NULL;
}

void *swap_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    int thread_id = td->thread_id - SWAP1;
    while (running) {
        custom_mutex_lock(&global_mutex);
        (*counter)++;
        custom_mutex_unlock(&global_mutex);
        int list_length = get_list_length(storage);
        if (list_length < 3) { usleep(1000); continue; }
        int pos = rand() % (list_length - 2);
        custom_mutex_lock(&storage->head_mutex);
        Node *first = storage->first;
        if (!first) { custom_mutex_unlock(&storage->head_mutex); usleep(1000); continue; }
        custom_mutex_lock(&first->sync);
        custom_mutex_unlock(&storage->head_mutex);
        Node *second = NULL, *third = NULL;
        int found = 0;
        for (int i = 0; i < pos && first && first->next; i++) {
            second = first->next;
            custom_mutex_lock(&second->sync);
            if (i == pos - 1 && second->next) {
                third = second->next;
                custom_mutex_lock(&third->sync);
                found = 1;
                break;
            }
            custom_mutex_unlock(&first->sync);
            first = second;
        }
        if (!found) {
            custom_mutex_unlock(&first->sync);
            if (second) custom_mutex_unlock(&second->sync);
            usleep(1000);
            continue;
        }
        if (first->next == second && second->next == third && (rand() % 2)) {
            if (pos == 0) custom_mutex_lock(&storage->head_mutex);
            second->next = third->next;
            third->next = second;
            first->next = third;
            if (pos == 0) {
                storage->first = third;
                custom_mutex_unlock(&storage->head_mutex);
            }
            custom_mutex_lock(&global_mutex);
            swap_counts[thread_id]++;
            custom_mutex_unlock(&global_mutex);
        }
        custom_mutex_unlock(&third->sync);
        custom_mutex_unlock(&second->sync);
        custom_mutex_unlock(&first->sync);
        usleep(1000);
    }
    return NULL;
}

void *count_monitor(void *arg) {
    int *counters = (int *)arg;
    int iterations = 0;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    while (running && iterations < 20) {
        printf("Iteration %d (CUSTOM MUTEX)\n", iterations + 1);
        printf("Iterations: ASC=%d, DESC=%d, EQ=%d, SWAP1=%d, SWAP2=%d, SWAP3=%d\n",
               counters[ASC], counters[DESC], counters[EQ],
               counters[SWAP1], counters[SWAP2], counters[SWAP3]);
        printf("Pairs: Ascending=%d, Descending=%d, Equal=%d\n",
               asc_pairs, desc_pairs, eq_pairs);
        printf("Swaps total: %d\n", swap_counts[0] + swap_counts[1] + swap_counts[2]);
        printf("---\n");
        sleep(1);
        iterations++;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    double total_iters = counters[ASC] + counters[DESC] + counters[EQ] +
                         counters[SWAP1] + counters[SWAP2] + counters[SWAP3];
    double throughput = total_iters / elapsed;
    printf("FINAL RESULTS (CUSTOM MUTEX)\n");
    printf("Time elapsed: %.2f sec\n", elapsed);
    printf("Total iterations: %.0f\n", total_iters);
    printf("Throughput: %.0f iterations/sec\n", throughput);
    printf("Final storage:\n");
    print_storage(global_storage);
    running = 0;
    return NULL;
}

int main(int argc, char *argv[]) {
    signal(SIGINT, handle_sigint);
    srand(time(NULL));
    int capacity = STORAGE_CAPACITY;
    if (argc > 1) {
        capacity = atoi(argv[1]);
        if (capacity < 10) capacity = STORAGE_CAPACITY;
    }
    printf("CUSTOM MUTEX VERSION - Capacity: %d\n", capacity);
    Storage *storage = initialize_storage(capacity);
    global_storage = storage;
    fill_storage(storage, capacity);
    printf("Initial storage:\n");
    print_storage(storage);
    pthread_t threads[THREAD_COUNT + 1];
    int counters[THREAD_COUNT] = {0};
    ThreadData thread_data[THREAD_COUNT];
    for (int i = 0; i < THREAD_COUNT; i++) {
        thread_data[i].storage = storage;
        thread_data[i].counter = &counters[i];
        thread_data[i].thread_id = i;
    }
    pthread_create(&threads[ASC], NULL, ascending_thread, &thread_data[ASC]);
    pthread_create(&threads[DESC], NULL, descending_thread, &thread_data[DESC]);
    pthread_create(&threads[EQ], NULL, equal_length_thread, &thread_data[EQ]);
    pthread_create(&threads[SWAP1], NULL, swap_thread, &thread_data[SWAP1]);
    pthread_create(&threads[SWAP2], NULL, swap_thread, &thread_data[SWAP2]);
    pthread_create(&threads[SWAP3], NULL, swap_thread, &thread_data[SWAP3]);
    pthread_create(&threads[THREAD_COUNT], NULL, count_monitor, counters);
    for (int i = 0; i < THREAD_COUNT; i++) {
            pthread_join(threads[i], NULL);
    }
    pthread_join(threads[THREAD_COUNT], NULL);
    free_storage(storage);
    printf("Program finished.\n");
    return 0;
}

#ifndef QUEUE_H
#define QUEUE_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#define MAX_STRING_LENGTH 100

typedef struct _Node {
    char value[MAX_STRING_LENGTH];
    struct _Node *next;
    pthread_spinlock_t sync;
} Node;

typedef struct _Storage {
    Node *first;
    int capacity;  
    pthread_mutex_t head_mutex;
} Storage;

typedef struct _ThreadData {
    Storage *storage;
    int *counter;
    int thread_id;
} ThreadData;

extern int asc_pairs;
extern int desc_pairs;
extern int eq_pairs;
extern int swap_counts[3];
extern pthread_mutex_t global_mutex;

Storage* initialize_storage(int capacity);
void add_node(Storage *storage, const char *value);
void fill_storage(Storage *storage, int capacity);
void print_storage(Storage *storage);
void free_storage(Storage *storage);
int get_list_length(Storage *storage);

#endif

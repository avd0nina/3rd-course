#include "queue.h"

pthread_mutex_t global_mutex = PTHREAD_MUTEX_INITIALIZER;
int asc_pairs = 0;
int desc_pairs = 0;
int eq_pairs = 0;
int swap_counts[3] = {0, 0, 0};

Storage* initialize_storage(int capacity) {
    Storage *storage = malloc(sizeof(Storage));
    if (!storage) {
        printf("Memory allocation failed\n");
        abort();
    }
    storage->first = NULL;
    storage->capacity = capacity;
    pthread_mutex_init(&storage->head_mutex, NULL);
    return storage;
}

void add_node(Storage *storage, const char *value) {
    Node *new_node = malloc(sizeof(Node));
    if (!new_node) {
        perror("Memory allocation failed");
        exit(EXIT_FAILURE);
    }
    strncpy(new_node->value, value, MAX_STRING_LENGTH - 1);
    new_node->value[MAX_STRING_LENGTH - 1] = '\0';
    new_node->next = NULL;
    pthread_spin_init(&new_node->sync, PTHREAD_PROCESS_PRIVATE);  
    
    pthread_mutex_lock(&storage->head_mutex);
    if (storage->first == NULL) {
        storage->first = new_node;
    } else {
        Node *current = storage->first;
        while (current->next != NULL) {
            current = current->next;
        }
        current->next = new_node;
    }
    pthread_mutex_unlock(&storage->head_mutex);
}

void fill_storage(Storage *storage, int capacity) {
    for (int i = 0; i < capacity; ++i) {
        int length = (i % 99) + 1;
        char value[MAX_STRING_LENGTH];
        memset(value, 'A' + (i % 26), length);
        value[length] = '\0';
        add_node(storage, value);
    }
}

void print_storage(Storage *storage) {
    pthread_mutex_lock(&storage->head_mutex);
    Node *current = storage->first;
    pthread_mutex_unlock(&storage->head_mutex);
    
    int count = 0;
    while (current != NULL && count < 20) {
        printf("%s(len=%zu) ", current->value, strlen(current->value));
        current = current->next;
        count++;
    }
    if (current != NULL) {
        printf("... and more elements\n");
    } else {
        printf("\n");
    }
}

int get_list_length(Storage *storage) {
    int length = 0;
    pthread_mutex_lock(&storage->head_mutex);
    Node *curr = storage->first;
    if (!curr) {
        pthread_mutex_unlock(&storage->head_mutex);
        return 0;
    }
    pthread_spin_lock(&curr->sync);
    pthread_mutex_unlock(&storage->head_mutex);

    while (curr != NULL) {
        Node *next = curr->next;
        if (next) {
            pthread_spin_lock(&next->sync);
        }
        length++;
        pthread_spin_unlock(&curr->sync);
        curr = next;
    }
    return length;
}

void free_storage(Storage *storage) {
    Node *current = storage->first;
    while (current != NULL) {
        Node *next = current->next;
        pthread_spin_destroy(&current->sync);
        free(current);
        current = next;
    }
    pthread_mutex_destroy(&storage->head_mutex);
    free(storage);
}

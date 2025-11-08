#include "queue.h"
#include <time.h>

/**
 * Константы для настройки программы.
 */
#define STORAGE_CAPACITY 5       ///< Дефолтная ёмкость списка
#define THREAD_COUNT 6                 ///< Количество рабочих потоков
#define ASC 0                          ///< Идентификатор потока ASC
#define DESC 1                         ///< Идентификатор потока DESC
#define EQ 2                           ///< Идентификатор потока EQ
#define SWAP1 3                        ///< Идентификатор потока SWAP1
#define SWAP2 4                        ///< Идентификатор потока SWAP2
#define SWAP3 5                        ///< Идентификатор потока SWAP3

/** Флаг выполнения потоков (volatile — асинхронное изменение). */
volatile int running = 1;
int asc_nodes_read = 0, desc_nodes_read = 0, eq_nodes_read = 0;
/**
 * Поток, считающий пары по возрастанию длин.
 * Проходит по списку, считает пары, где длина текущей строки меньше следующей.
 * @param data Указатель на ThreadData.
 * @return NULL
 */
void *ascending_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        int nodes_read = 0;  // ← Считаем
        pthread_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        if (curr == NULL) {
            pthread_mutex_unlock(&storage->head_mutex);
            usleep(1);
            continue;
        }
        pthread_rwlock_rdlock(&curr->sync);
        pthread_mutex_unlock(&storage->head_mutex);
        Node *next = curr->next;
        nodes_read = 1;  // первый узел
        while (next != NULL && running) {
            pthread_rwlock_rdlock(&next->sync);
            nodes_read++;  // ← каждый новый узел
            if (strlen(curr->value) < strlen(next->value)) {
                local_count++;
            }
            pthread_rwlock_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        pthread_rwlock_unlock(&curr->sync);
        pthread_mutex_lock(&global_mutex);
        asc_pairs = local_count;
        asc_nodes_read = nodes_read;  // ← Сохраняем
        (*counter)++;
        pthread_mutex_unlock(&global_mutex);
        usleep(1);
    }
    return NULL;
}

/**
 * Поток, считающий пары по убыванию длин.
 * Аналогичен ascending_thread, но сравнивает curr > next.
 */
void *descending_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        int nodes_read = 0;
        pthread_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        if (curr == NULL) {
            pthread_mutex_unlock(&storage->head_mutex);
            usleep(1);
            continue;
        }
        pthread_rwlock_rdlock(&curr->sync);
        pthread_mutex_unlock(&storage->head_mutex);
        Node *next = curr->next;
        nodes_read = 1;  // первый узел
        while (next != NULL && running) {
            pthread_rwlock_rdlock(&next->sync);
            nodes_read++;  // ← каждый новый узел
            if (strlen(curr->value) > strlen(next->value)) {
                local_count++;
            }
            pthread_rwlock_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        pthread_rwlock_unlock(&curr->sync);
        pthread_mutex_lock(&global_mutex);
        desc_pairs = local_count;
        desc_nodes_read = nodes_read;  // ← Сохраняем
        (*counter)++;
        pthread_mutex_unlock(&global_mutex);
        usleep(1);
    }
    return NULL;
}

/**
 * Поток, считающий пары с равной длиной.
 * Аналогичен предыдущим, но сравнивает curr == next.
 */
void *equal_length_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    while (running) {
        int local_count = 0;
        int nodes_read = 0;
        pthread_mutex_lock(&storage->head_mutex);
        Node *curr = storage->first;
        if (curr == NULL) {
            pthread_mutex_unlock(&storage->head_mutex);
            usleep(1);
            continue;
        }
        pthread_rwlock_rdlock(&curr->sync);
        pthread_mutex_unlock(&storage->head_mutex);
        Node *next = curr->next;
        nodes_read = 1;  // первый узел
        while (next != NULL && running) {
            pthread_rwlock_rdlock(&next->sync);
            nodes_read++;  // ← каждый новый узел
            if (strlen(curr->value) == strlen(next->value)) {
                local_count++;
            }
            pthread_rwlock_unlock(&curr->sync);
            curr = next;
            next = curr->next;
        }
        pthread_rwlock_unlock(&curr->sync);
        pthread_mutex_lock(&global_mutex);
        eq_pairs = local_count;
        eq_nodes_read = nodes_read;  // ← Сохраняем
        (*counter)++;
        pthread_mutex_unlock(&global_mutex);
        usleep(1);
    }
    return NULL;
}

/**
 * Поток, меняющий местами два соседних узла.
 * Выбирает случайную тройку узлов (prev, A, B), меняет A и B.
 */
void *swap_thread(void *data) {
    ThreadData *td = (ThreadData *)data;
    Storage *storage = td->storage;
    int *counter = td->counter;
    int thread_id = td->thread_id - SWAP1;  // 0, 1, 2
    while (running) {
        // Увеличиваем счётчик итераций
        pthread_mutex_lock(&global_mutex);
        (*counter)++;
        pthread_mutex_unlock(&global_mutex);
        int list_length = get_list_length(storage);
        if (list_length < 3) {  // Нужно минимум 3 узла для swap
            usleep(1000);
            continue;
        }
        int pos = rand() % (list_length - 2);  // Случайная позиция prev
        // Получаем первый узел
        pthread_mutex_lock(&storage->head_mutex);
        Node *first = storage->first;
        if (first == NULL) {
            pthread_mutex_unlock(&storage->head_mutex);
            usleep(1000);
            continue;
        }
        pthread_rwlock_wrlock(&first->sync);
        pthread_mutex_unlock(&storage->head_mutex);
        Node *second = NULL;
        Node *third = NULL;
        int found = 0;
        // Проход до позиции pos
        for (int i = 0; i < pos && first && first->next; i++) {
            second = first->next;
            pthread_rwlock_wrlock(&second->sync);
            if (i == pos - 1 && second->next != NULL) {
                third = second->next;
                pthread_rwlock_wrlock(&third->sync);
                found = 1;
                break;
            }
            pthread_rwlock_unlock(&first->sync);
            first = second;
        }
        if (!found) {
            pthread_rwlock_unlock(&first->sync);
            if (second) pthread_rwlock_unlock(&second->sync);
            usleep(1000);
            continue;
        }
        // Проверяем целостность
        if (first->next == second && second->next == third) {
            int should_swap = rand() % 2;  // 50% шанс
            if (should_swap) {
                if (pos == 0) {  // Меняем голову списка
                    pthread_mutex_lock(&storage->head_mutex);
                }
                // Swap: first → second → third → X → first → third → second → X
                second->next = third->next;
                third->next = second;
                first->next = third;
                if (pos == 0) {
                    storage->first = third;
                    pthread_mutex_unlock(&storage->head_mutex);
                }
                pthread_mutex_lock(&global_mutex);
                swap_counts[thread_id]++;
                pthread_mutex_unlock(&global_mutex);
            }
        }
        // Освобождаем rwlock'и в обратном порядке
        pthread_rwlock_unlock(&third->sync);
        pthread_rwlock_unlock(&second->sync);
        pthread_rwlock_unlock(&first->sync);
        usleep(1000);
    }
    return NULL;
}

/**
 * Монитор: печатает статистику каждые 2 секунды. После 20 итераций останавливает все потоки.
 */
void *count_monitor(void *arg) {
    int *counters = (int *)arg;
    int iterations = 0;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    while (running && iterations < 20) {
        printf("Iteration %d (RWLOCK)\n", iterations + 1);
        printf("Iterations: ASC=%d, DESC=%d, EQ=%d, SWAP1=%d, SWAP2=%d, SWAP3=%d\n",
               counters[ASC], counters[DESC], counters[EQ],
               counters[SWAP1], counters[SWAP2], counters[SWAP3]);
        printf("Pairs: Ascending=%d, Descending=%d, Equal=%d (read %d, %d, %d nodes)\n",
               asc_pairs, desc_pairs, eq_pairs,
               asc_nodes_read, desc_nodes_read, eq_nodes_read);
        printf("Swaps total: %d\n",
               swap_counts[0] + swap_counts[1] + swap_counts[2]);
        sleep(2);
        iterations++;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    double throughput = (counters[ASC] + counters[DESC] + counters[EQ] +
                        counters[SWAP1] + counters[SWAP2] + counters[SWAP3]) / elapsed;
    printf("Time elapsed: %.2f sec | Throughput: %.0f iterations/sec\n", elapsed, throughput);
    running = 0;
    return NULL;
}

/**
 * Главная функция.
 * Создаёт список, запускает потоки, ждёт монитор, выводит результат.
 */
int main(int argc, char *argv[]) {
    srand(time(NULL));  // Инициализация ГСЧ
    int capacity = STORAGE_CAPACITY;
    if (argc > 1) {
        capacity = atoi(argv[1]);
        if (capacity < 10) capacity = STORAGE_CAPACITY;
    }
    printf("RWLOCK VERSION - Capacity: %d\n", capacity);
    Storage *storage = initialize_storage(capacity);
    fill_storage(storage, capacity);
    printf("Initial storage:\n");
    print_storage(storage);
    pthread_t threads[THREAD_COUNT + 1];  // 6 рабочих + 1 монитор
    int counters[THREAD_COUNT] = {0};     // Счётчики итераций
    ThreadData thread_data[THREAD_COUNT];
    // Инициализация данных для потоков
    for (int i = 0; i < THREAD_COUNT; i++) {
        thread_data[i].storage = storage;
        thread_data[i].counter = &counters[i];
        thread_data[i].thread_id = i;
    }
    // Запуск потоков
    pthread_create(&threads[ASC], NULL, ascending_thread, &thread_data[ASC]);
    pthread_create(&threads[DESC], NULL, descending_thread, &thread_data[DESC]);
    pthread_create(&threads[EQ], NULL, equal_length_thread, &thread_data[EQ]);
    pthread_create(&threads[SWAP1], NULL, swap_thread, &thread_data[SWAP1]);
    pthread_create(&threads[SWAP2], NULL, swap_thread, &thread_data[SWAP2]);
    pthread_create(&threads[SWAP3], NULL, swap_thread, &thread_data[SWAP3]);
    pthread_create(&threads[THREAD_COUNT], NULL, count_monitor, counters);
    // Ожидание завершения монитора
    pthread_join(threads[THREAD_COUNT], NULL);
    sleep(1);
    printf("FINAL RESULTS (RWLOCK)\n");
    printf("Final storage:\n");
    print_storage(storage);
    free_storage(storage);
    pthread_mutex_destroy(&global_mutex);
    printf("Program finished.\n");
    return 0;
}

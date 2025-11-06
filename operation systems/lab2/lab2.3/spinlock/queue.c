#include "queue.h"

/**
 * Глобальный мьютекс для защиты счётчиков статистики.
 * Защищает доступ к переменным asc_pairs, desc_pairs, eq_pairs и swap_counts[3] от одновременного изменения несколькими потоками.
 */
pthread_mutex_t global_mutex = PTHREAD_MUTEX_INITIALIZER;

/** Счётчик пар по возрастанию длин. */
int asc_pairs = 0;
/** Счётчик пар по убыванию длин. */
int desc_pairs = 0;
/** Счётчик пар с равной длиной. */
int eq_pairs = 0;
/** Счётчики успешных перестановок для трёх swap-потоков. */
int swap_counts[3] = {0, 0, 0};

/**
 * Создаёт и инициализирует хранилище списка.
 * Выделяет память под структуру Storage, инициализирует указатель на первый узел, сохраняет ёмкость и инициализирует мьютекс головы.
 * @param capacity Количество узлов в списке.
 * @return Указатель на созданное хранилище.
 */
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

/**
 * Добавляет новый узел в конец списка.
 * Выделяет память под узел, копирует строку, инициализирует спинлок узла и вставляет его в конец списка под защитой head_mutex.
 * @param storage Указатель на хранилище.
 * @param value Строка для копирования в узел.
 */
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

/**
 * Заполняет список capacity узлами.
 * Создаёт строки с длинами 1..99 и символами 'A'..'Z' по циклу. Использует add_node() для вставки.
 * @param storage Указатель на хранилище.
 * @param capacity Количество узлов.
 */
void fill_storage(Storage *storage, int capacity) {
    for (int i = 0; i < capacity; ++i) {
        int length = (i % 99) + 1;
        char value[MAX_STRING_LENGTH];
        memset(value, 'A' + (i % 26), length);
        value[length] = '\0';
        add_node(storage, value);
    }
}

/**
 * Печатает первые 20 узлов списка. Копирует указатель на первый узел под защитой head_mutex, затем выводит строки с их длинами.
 * @param storage Указатель на хранилище.
 */
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

/**
 * Возвращает длину списка с hand-over-hand locking.
 * Использует head_mutex для получения первого узла, затем передаёт эстафету спинлокам узлов. Безопасно при параллельных swap'ах.
 * @param storage Указатель на хранилище.
 * @return Количество узлов в списке.
 */
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

/**
 * Освобождает всю память, занятую списком.
 * Проходит по списку, уничтожает спинлоки узлов, освобождает память узлов и хранилища.
 * @param storage Указатель на хранилище.
 */
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

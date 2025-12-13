#include "cache.h"

#include <errno.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include <unistd.h>

#include "../include/log.h"

#define MIN(x, y) (x < y) ? x : y

/**
 * @brief Узел хэш-таблицы кэша
 * @details Связывает элемент кэша с дополнительной информацией:
 *          временем последнего изменения и блокировкой для чтения/записи.
 * @var entry                Указатель на основной элемент кэша (cache_entry_t)
 * @var last_modified_time   Время последнего доступа/изменения элемента
 * @var rwlock               Читательско-писательская блокировка для узла
 * @var next                 Указатель на следующий узел в цепочке коллизий
 * @var lru_prev             Указатель на предыдущий узел в LRU-списке
 * @var lru_next             Указатель на следующий узел в LRU-списке
 */
typedef struct cache_node_t {
    cache_entry_t *entry;
    struct timeval last_modified_time;
    pthread_rwlock_t rwlock;
    struct cache_node_t *next;
    struct cache_node_t *lru_prev;
    struct cache_node_t *lru_next;
} cache_node_t;

/**
 * @brief Основная структура кэша
 * @details Реализует кэш как хэш-таблицу с garbage collector'ом
 * @var capacity                      Вместимость хэш-таблицы (число слотов)
 * @var array                         Массив указателей на цепочки узлов (хэш-таблица)
 * @var garbage_collector_running     Атомарный флаг работы сборщика мусора
 * @var entry_expired_time_ms         Время жизни элемента кэша в миллисекундах
 * @var garbage_collector             Дескриптор потока сборщика мусора
 * @var current_size                  Текущее количество элементов в кэше (атомарный)
 * @var lru_mutex                     Мьютекс для синхронизации LRU-операций
 * @var lru_head                      head для LRU list
 * @var lru_tail                      tail для LRU list
 */
struct cache_t {
    int capacity;
    cache_node_t **array;
    atomic_int garbage_collector_running;
    time_t entry_expired_time_ms;
    pthread_t garbage_collector;
    atomic_int current_size;
    pthread_mutex_t lru_mutex;
    cache_node_t *lru_head;
    cache_node_t *lru_tail;
};

/**
 * @brief Вычисляет хэш для HTTP-запроса
 * @param request      Текст HTTP-запроса
 * @param request_len  Длина запроса в байтах
 * @param size         Размер хэш-таблицы (для получения индекса в массиве)
 * @return Индекс в хэш-таблице (от 0 до size-1)
 * @details Использует простую хэш-функцию: сумма байтов по модулю size
 */
static int hash(const char *request, size_t request_len, int size);

/**
 * @brief Создает новый узел хэш-таблицы
 * @param entry Указатель на элемент кэша для хранения в узле
 * @return Указатель на созданный узел или NULL при ошибке
 * @details Инициализирует время последнего изменения текущим временем
 *          и создает rwlock для узла.
 */
static cache_node_t *cache_node_create(cache_entry_t *entry);

/**
 * @brief Уничтожает узел хэш-таблицы
 * @param node Узел для уничтожения
 * @details Освобождает блокировку rwlock, но НЕ освобождает cache_entry_t.
 *          Ответственность за освобождение cache_entry_t лежит на вызывающей стороне.
 */
static void cache_node_destroy(cache_node_t *node);

/**
 * @brief Удаляет узел из LRU-списка
 * @param node Узел для удаления из списка
 */
static void _lru_remove(cache_node_t *node);

/**
 * @brief Перемещает узел в начало LRU-списка (most recently used)
 * @param cache Кэш
 * @param node Узел для перемещения
 */
static void move_to_head(cache_t *cache, cache_node_t *node);

/**
 * @brief Удаляет и вытесняет наименее недавно использованный элемент (tail)
 * @param cache Кэш
 */
static void remove_tail(cache_t *cache);

/**
 * @brief Функция потока garbage collector'а
 * @param arg Указатель на структуру cache_t
 * @details Бесконечный цикл, который периодически проверяет все элементы кэша
 *          и удаляет те, которые не использовались дольше entry_expired_time_ms.
 *          Работает в фоновом режиме, пока garbage_collector_running == 1.
 */
static void *garbage_collector_routine(void *arg);

/**
 * @brief Вычисляет хэш для HTTP-запроса
 * @param request      Текст HTTP-запроса
 * @param request_len  Длина запроса в байтах
 * @param size         Размер хэш-таблицы (для получения индекса в массиве)
 * @return Индекс в хэш-таблице (от 0 до size-1)
 * @details Использует простую хэш-функцию: сумма байтов по модулю size
 */
static int hash(const char *request, size_t request_len, int size) {
    int sum = 0;
    for (size_t i = 0; i < request_len; i++) sum += request[i];
    return sum % size;
}

/**
 * @brief Создает новый узел хэш-таблицы
 * @param entry Указатель на элемент кэша для хранения в узле
 * @return Указатель на созданный узел или NULL при ошибке
 * @details Инициализирует время последнего изменения текущим временем
 *          и создает rwlock для узла.
 */
static cache_node_t *cache_node_create(cache_entry_t *entry) {
    errno = 0;
    cache_node_t *node = malloc(sizeof(cache_node_t));
    if (node == NULL) {
        proxy_log("Cache node creation error: %s", strerror(errno));
        return NULL;
    }
    node->entry = entry;
    gettimeofday(&node->last_modified_time, 0);
    pthread_rwlock_init(&node->rwlock, NULL);
    node->next = NULL;
    node->lru_prev = NULL;
    node->lru_next = NULL;
    return node;
}

/**
 * @brief Уничтожает узел хэш-таблицы
 * @param node Узел для уничтожения
 * @details Освобождает блокировку rwlock, но НЕ освобождает cache_entry_t.
 *          Ответственность за освобождение cache_entry_t лежит на вызывающей стороне.
 */
static void cache_node_destroy(cache_node_t *node) {
    if (node == NULL) {
        proxy_log("Cache node destroying error: node is NULL");
        return;
    }
    cache_entry_destroy(node->entry);
    pthread_rwlock_destroy(&node->rwlock);
    free(node);
}

/**
 * @brief Удаляет узел из LRU-списка
 * @param node Узел для удаления из списка
 */
static void _lru_remove(cache_node_t *node) {
    if (node == NULL) return;
    node->lru_prev->lru_next = node->lru_next;
    node->lru_next->lru_prev = node->lru_prev;
    node->lru_prev = NULL;
    node->lru_next = NULL;
}

/**
 * @brief Перемещает узел в начало LRU-списка (most recently used)
 * @param cache Кэш
 * @param node Узел для перемещения
 */
static void move_to_head(cache_t *cache, cache_node_t *node) {
    pthread_mutex_lock(&cache->lru_mutex);
    _lru_remove(node);
    node->lru_next = cache->lru_head->lru_next;
    node->lru_next->lru_prev = node;
    cache->lru_head->lru_next = node;
    node->lru_prev = cache->lru_head;
    pthread_mutex_unlock(&cache->lru_mutex);
}

/**
 * @brief Удаляет и вытесняет наименее недавно использованный элемент (tail)
 * @param cache Кэш
 */
static void remove_tail(cache_t *cache) {
    pthread_mutex_lock(&cache->lru_mutex);
    cache_node_t *tail = cache->lru_tail->lru_prev;
    if (tail == cache->lru_head) {
        // Список пуст
        pthread_mutex_unlock(&cache->lru_mutex);
        return;
    }
    _lru_remove(tail);
    pthread_mutex_unlock(&cache->lru_mutex);
    // Удаляем элемент из кэша
    cache_delete(cache, tail->entry->request, tail->entry->request_len);
}

/**
 * @brief Создает новый кэш с указанными параметрами
 * @param capacity              Максимальное количество элементов
 * @param cache_expired_time_ms Время жизни элемента в миллисекундах
 * @return Указатель на созданный кэш или NULL при ошибке
 */
cache_t *cache_create(int capacity, time_t cache_expired_time_ms) {
    errno = 0;
    cache_t *cache = malloc(sizeof(cache_t));
    if (cache == NULL) {
        proxy_log("Cache creation error: %s", strerror(errno));
        return NULL;
    }
    cache->capacity = capacity;
    cache->array = calloc(capacity, sizeof(cache_node_t *));
    if (cache->array == NULL) {
        proxy_log("Cache creation error: %s", strerror(errno));
        free(cache);
        return NULL;
    }
    atomic_store(&cache->garbage_collector_running, 1);
    cache->entry_expired_time_ms = cache_expired_time_ms;
    atomic_store(&cache->current_size, 0);
    // Инициализация LRU
    pthread_mutex_init(&cache->lru_mutex, NULL);
    cache->lru_head = cache_node_create(NULL);
    cache->lru_tail = cache_node_create(NULL);
    if (cache->lru_head == NULL || cache->lru_tail == NULL) {
        proxy_log("Cache creation error: failed to create dummy LRU nodes");
        free(cache->array);
        free(cache);
        return NULL;
    }
    cache->lru_head->lru_next = cache->lru_tail;
    cache->lru_tail->lru_prev = cache->lru_head;
    // Запуск GC
    if (pthread_create(&cache->garbage_collector, NULL, garbage_collector_routine, cache) != 0) {
        proxy_log("Cache creation error: failed to create garbage collector thread");
        free(cache->array);
        free(cache);
        return NULL;
    }
    return cache;
}

/**
 * @brief Ищет элемент кэша по запросу
 * @details Если элемент найден но еще загружается, блокирует поток до готовности
 * @param cache        Кэш для поиска
 * @param request      Текст запроса для поиска
 * @param request_len  Длина запроса
 * @return Указатель на найденный элемент или NULL если не найден
 */
cache_entry_t *cache_get(cache_t *cache, const char *request, size_t request_len) {
    if (cache == NULL || request == NULL) return NULL;
    int index = hash(request, request_len, cache->capacity);
    cache_node_t *curr = cache->array[index];
    while (curr != NULL) {
        pthread_rwlock_rdlock(&curr->rwlock);
        if (curr->entry->request_len == request_len && strncmp(curr->entry->request, request, request_len) == 0 && !curr->entry->deleted) {
            gettimeofday(&curr->last_modified_time, 0);
            // Обновляем LRU: перемещаем в голову
            move_to_head(cache, curr);
            cache_entry_t *entry = curr->entry;
            pthread_rwlock_unlock(&curr->rwlock);
            return entry;
        }
        pthread_rwlock_unlock(&curr->rwlock);
        curr = curr->next;
    }
    return NULL;
}

/**
 * @brief Добавляет новый элемент в кэш
 * @param cache Кэш для добавления
 * @param entry Элемент для добавления
 * @return SUCCESS при успешном добавлении, ERROR при ошибке
 */
int cache_add(cache_t *cache, cache_entry_t *entry) {
    if (cache == NULL || entry == NULL) return ERROR;
    cache_node_t *node = cache_node_create(entry);
    if (node == NULL) return ERROR;
    int index = hash(entry->request, entry->request_len, cache->capacity);
    pthread_rwlock_wrlock(&node->rwlock); // Блокировка нового узла
    node->next = cache->array[index];
    cache->array[index] = node;
    pthread_rwlock_unlock(&node->rwlock);
    // Добавляем в голову LRU
    pthread_mutex_lock(&cache->lru_mutex);
    node->lru_next = cache->lru_head->lru_next;
    node->lru_next->lru_prev = node;
    cache->lru_head->lru_next = node;
    node->lru_prev = cache->lru_head;
    atomic_fetch_add(&cache->current_size, 1);
    pthread_mutex_unlock(&cache->lru_mutex);
    // Проверяем переполнение и вытесняем если нужно
    while (atomic_load(&cache->current_size) > cache->capacity) {
        remove_tail(cache);
    }
    return SUCCESS;
}

/**
 * @brief Удаляет элемент из кэша по запросу
 * @param cache        Кэш для удаления
 * @param request      Текст запроса для удаления
 * @param request_len  Длина запроса
 * @return SUCCESS при успешном удалении, ERROR или NOT_FOUND при ошибке
 */
int cache_delete(cache_t *cache, const char *request, size_t request_len) {
    if (cache == NULL || request == NULL) return ERROR;
    int index = hash(request, request_len, cache->capacity);
    cache_node_t *curr = cache->array[index];
    cache_node_t *prev = NULL;
    while (curr != NULL) {
        pthread_rwlock_rdlock(&curr->rwlock);
        if (curr->entry->request_len == request_len && strncmp(curr->entry->request, request, request_len) == 0) {
            // Удаляем из LRU сначала
            pthread_mutex_lock(&cache->lru_mutex);
            _lru_remove(curr);
            atomic_fetch_sub(&cache->current_size, 1);
            pthread_mutex_unlock(&cache->lru_mutex);
            // Удаляем из цепочки хэш-таблицы
            if (prev == NULL) {
                cache->array[index] = curr->next;
            } else {
                prev->next = curr->next;
            }
            pthread_rwlock_unlock(&curr->rwlock);
            curr->entry->deleted = 1;
            pthread_cond_broadcast(&curr->entry->ready_cond);
            cache_node_destroy(curr);
            return SUCCESS;
        }
        pthread_rwlock_unlock(&curr->rwlock);
        prev = curr;
        curr = curr->next;
    }
    return NOT_FOUND;
}

/**
 * @brief Полностью уничтожает кэш, освобождая все ресурсы
 * @param cache Кэш для уничтожения
 */
void cache_destroy(cache_t *cache) {
    if (cache == NULL) return;
    atomic_store(&cache->garbage_collector_running, 0);
    pthread_join(cache->garbage_collector, NULL);
    for (int i = 0; i < cache->capacity; i++) {
        cache_node_t *curr = cache->array[i];
        while (curr != NULL) {
            cache_node_t *next = curr->next;
            // Удаляем из LRU (хотя список уже пустеет)
            _lru_remove(curr);
            cache_node_destroy(curr);
            curr = next;
        }
    }
    // Уничтожаем dummy nodes
    free(cache->lru_head);
    free(cache->lru_tail);
    pthread_mutex_destroy(&cache->lru_mutex);
    free(cache->array);
    free(cache);
}

/**
 * @brief Функция потока garbage collector'а
 * @param arg Указатель на структуру cache_t
 * @details Бесконечный цикл, который периодически проверяет все элементы кэша
 *          и удаляет те, которые не использовались дольше entry_expired_time_ms.
 *          Работает в фоновом режиме, пока garbage_collector_running == 1.
 */
static void *garbage_collector_routine(void *arg) {
    pthread_setname_np("garbage-collector");
    if (arg == NULL) {
        proxy_log("Cache garbage collector error: cache is NULL");
        pthread_exit(NULL);
    }
    cache_t *cache = (cache_t *) arg;
    proxy_log("Cache garbage collector start");
    struct timeval curr_time;
    while (atomic_load(&cache->garbage_collector_running)) {
        usleep(MIN(1000 * cache->entry_expired_time_ms / 2, 1000000)); // Проверяем элементы в 2 раза чаще чем время их жизни
        proxy_log("Garbage collector running");
        gettimeofday(&curr_time, 0);
        for (int i = 0; i < cache->capacity; i++) { // Проход по всем индексам
            cache_node_t *curr = cache->array[i]; // Первый элемент в цепочке
            if (curr == NULL) continue;
            cache_node_t *next = NULL; // Указатель на следующий узел
            while (curr != NULL) {
                pthread_rwlock_rdlock(&curr->rwlock);
                time_t diff = (curr_time.tv_sec - curr->last_modified_time.tv_sec) * 1000 +
                              (curr_time.tv_usec - curr->last_modified_time.tv_usec) / 1000; // Вычисление времени, прошедшего с последнего доступа
                next = curr->next; // Получение следующего элемента
                pthread_rwlock_unlock(&curr->rwlock);
                if (diff >= cache->entry_expired_time_ms) { // Проверка истекло ли время жизни элемента
                    cache_delete(cache, curr->entry->request, curr->entry->request_len); // Удаление элемента
                }
                curr = next;
            }
        }
    }
    proxy_log("Cache garbage collector destroy");
    pthread_exit(NULL);
}

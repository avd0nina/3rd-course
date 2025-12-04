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
 */
typedef struct cache_node_t {
    cache_entry_t *entry;
    struct timeval last_modified_time;
    pthread_rwlock_t rwlock;
    struct cache_node_t *next;
} cache_node_t;

/**
 * @brief Основная структура кэша
 * @details Реализует кэш как хэш-таблицу с garbage collector'ом
 * @var capacity                      Вместимость хэш-таблицы
 * @var array                         Массив указателей на цепочки узлов (хэш-таблица)
 * @var garbage_collector_running     Атомарный флаг работы сборщика мусора
 * @var entry_expired_time_ms         Время жизни элемента кэша в миллисекундах
 * @var garbage_collector             Дескриптор потока сборщика мусора
 */
struct cache_t {
    int capacity;
    cache_node_t **array;
    atomic_int garbage_collector_running;
    time_t entry_expired_time_ms;
    pthread_t garbage_collector;
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
 * @brief Функция потока garbage collector'а
 * @param arg Указатель на структуру cache_t
 * @details Бесконечный цикл, который периодически проверяет все элементы кэша
 *          и удаляет те, которые не использовались дольше entry_expired_time_ms.
 *          Работает в фоновом режиме, пока garbage_collector_running == 1.
 */
static void *garbage_collector_routine(void *arg);

/**
 * @brief Создает и инициализирует новую структуру кэша
 * @param capacity  Вместимость
 * @param cache_expired_time_ms Время жизни элемента в миллисекундах
 * @return Указатель на созданный кэш или NULL при ошибке
 * @details Выполняет следующие шаги:
 *          1. Выделяет память под основную структуру cache_t
 *          2. Инициализирует поля структуры
 *          3. Создает хэш-таблицу (массив указателей)
 *          4. Запускает поток garbage collector'а
 *          5. Устанавливает имя потоку для отладки
 */
cache_t *cache_create(int capacity, time_t cache_expired_time_ms) {
    errno = 0;
    cache_t *cache = malloc(sizeof(cache_t)); // выделяем память для основной структуры кэша
    if (cache == NULL) {
        if (errno == ENOMEM) proxy_log("Cache creation error: %s", strerror(errno));
        else proxy_log("Cache creation error: failed to reallocate memory");
        return NULL;
    }
    cache->capacity = capacity;
    cache->entry_expired_time_ms = cache_expired_time_ms;
    cache->garbage_collector_running = 1;
    errno = 0;
    cache->array = calloc(sizeof(cache_node_t *), capacity); // выделяем память для хэш-таблицы и заполняем нулями
    if (cache->array == NULL) {
        if (errno == ENOMEM) proxy_log("Cache creation error: %s", strerror(errno));
        else proxy_log("Cache creation error: failed to reallocate memory");
        free(cache);
        return NULL;
    }
    for (int i = 0; i < capacity; i++) cache->array[i] = NULL; // устанавливает все элементы массива в NULL
    // Запуск потока garbage collector'а
    pthread_create(&cache->garbage_collector, NULL, garbage_collector_routine, cache); // Создает новый поток, который будет выполнять garbage_collector_routine
    // Установка имени потоку
    char thread_name[16];
    snprintf(thread_name, 16, "garbage-collector");
    pthread_setname_np(thread_name);
    return cache;
}

/**
 * @brief Ищет элемент кэша по HTTP-запросу
 * @param cache Указатель на структуру кэша
 * @param request Текст HTTP-запроса для поиска
 * @param request_len Длина запроса в байтах
 * @return Указатель на найденный элемент кэша или NULL если не найден
 * @details Алгоритм работы:
 *          1. Проверяет валидность указателя на кэш
 *          2. Вычисляет хэш запроса для определения индекса в хэш-таблице
 *          3. Итерируется по цепочке коллизий в найденном индексе
 *          4. Для каждого элемента сравнивает запросы
 *          5. При нахождении обновляет время последнего доступа
 *          6. Возвращает найденный элемент или NULL
 */
cache_entry_t *cache_get(cache_t *cache, const char *request, size_t request_len) {
    if (cache == NULL) {
        proxy_log("Cache getting error: cache is NULL");
        return NULL;
    }
    // Вычисление индекса в хэш-таблице
    int index = hash(request, request_len, cache->capacity);
    cache_node_t *curr = cache->array[index]; // Первый элемент в цепочке
    cache_node_t *prev = NULL; // Предыдущий элемент
    while (curr != NULL) { // Итерация по цепочке
        pthread_rwlock_rdlock(&curr->rwlock);
        if (curr->entry->request_len == request_len && strncmp(curr->entry->request, request, request_len) == 0) { // Проверяет, соответствует ли текущий элемент искомому запросу
            gettimeofday(&curr->last_modified_time, 0); // Обновляет время последнего доступа
            pthread_rwlock_unlock(&curr->rwlock);
            return curr->entry;
        }
        prev = curr;
        curr = curr->next; // Переход к следующему узлу
        pthread_rwlock_unlock(&prev->rwlock);
    }
    return NULL;
}

/**
 * @brief Добавляет новый элемент в кэш
 * @param cache Указатель на структуру кэша
 * @param entry Элемент кэша для добавления
 * @return SUCCESS при успешном добавлении, ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Проверяет валидность входных параметров
 *          2. Создает узел хэш-таблицы для элемента
 *          3. Вычисляет хэш для определения индекса в хэш-таблице
 *          4. Добавляет узел в начало цепочки соответствующего индекса
 *          5. Логирует операцию добавления
 */
int cache_add(cache_t *cache, cache_entry_t *entry) {
    if (cache == NULL) {
        proxy_log("Cache adding error: cache is NULL");
        return ERROR;
    }
    if (entry == NULL) {
        proxy_log("Cache adding error: cache entry is NULL");
        return ERROR;
    }
    cache_node_t *node = cache_node_create(entry); // Создание узла хэш-таблицы
    if (node == NULL) return ERROR;
    int index = hash(entry->request, entry->request_len, cache->capacity); // Вычисление индекса в хэш-таблице
    // Добавление узла в начало цепочки
    pthread_rwlock_wrlock(&node->rwlock);
    node->next = cache->array[index];
    pthread_rwlock_unlock(&node->rwlock);
    cache->array[index] = node;
    proxy_log("Add new cache entry");
    return SUCCESS;
}

/**
 * @brief Удаляет элемент из кэша по HTTP-запросу
 * @param cache Указатель на структуру кэша
 * @param request Текст HTTP-запроса для удаления
 * @param request_len Длина запроса в байтах
 * @return SUCCESS при успешном удалении, ERROR при ошибке, NOT_FOUND если элемент не найден
 * @details Алгоритм работы:
 *          1. Проверяет валидность указателя на кэш
 *          2. Вычисляет хэш запроса для определения индекса в хэш-таблице
 *          3. Итерируется по цепочке коллизий в найденном индексе
 *          4. Находит элемент по точному совпадению запроса
 *          5. Удаляет элемент из цепочки (с учетом что он может быть первым)
 *          6. Освобождает память узла и логирует операцию
 */
int cache_delete(cache_t *cache, const char *request, size_t request_len) {
    if (cache == NULL) {
        proxy_log("Cache deleting error: cache is NULL");
        return ERROR;
    }
    // Вычисление индекса в хэш-таблице
    int index = hash(request, request_len, cache->capacity);
    cache_node_t *curr = cache->array[index]; // Первый элемент в цепочке
    if (curr == NULL) return NOT_FOUND;
    cache_node_t *prev = NULL; // Предыдущий элемент
    while (curr != NULL) {
        pthread_rwlock_rdlock(&curr->rwlock);
        if (curr->entry->request_len == request_len && strncmp(curr->entry->request, request, request_len) == 0) { // Сравнивает запрос текущего узла с искомым
            if (prev == NULL) { // Если первый элемент
                cache_node_t *next = curr->next; // Получение следующего элемента
                if (next == NULL) cache->array[index] = NULL; // Если удаляемый элемент был единственным в цепочке Если удаляемый элемент был единственным в цепочке устанавливает array[index] в NULL.
            } else {
                pthread_rwlock_wrlock(&prev->rwlock);
                prev->next = curr->next; // Удаление элемента из середины списка
                pthread_rwlock_unlock(&prev->rwlock);
            }
            pthread_rwlock_unlock(&curr->rwlock);
            cache_node_destroy(curr); // Освобождает память, занятую структурой cache_node_t. cache_entry_t остается в памяти!
            proxy_log("Cache entry destroy");
            return SUCCESS;
        }
        prev = curr;
        curr = curr->next; // Переход к следующему узлу
        pthread_rwlock_unlock(&prev->rwlock);
    }
    return NOT_FOUND;
}

/**
 * @brief Полностью уничтожает кэш, освобождая все ресурсы
 * @param cache Указатель на структуру кэша для уничтожения
 * @details Алгоритм работы:
 *          1. Проверяет валидность указателя на кэш
 *          2. Останавливает поток garbage collector'а
 *          3. Ожидает завершения garbage collector'а
 *          4. Проходит по всем индексам хэш-таблицы
 *          5. Для каждого индекса удаляет все элементы цепочки
 *          6. Освобождает память хэш-таблицы и основной структуры
 */
void cache_destroy(cache_t *cache) {
    if (cache == NULL) {
        proxy_log("Cache destroying error: cache is NULL");
        return;
    }
    cache->garbage_collector_running = 0;
    pthread_join(cache->garbage_collector, NULL); // Блокирует текущий поток до тех пор, пока поток garbage collector'а не завершит свою работу
    for (int i = 0; i < cache->capacity; i++) { // Проход по всем индексам
        cache_node_t *curr = cache->array[i]; // Первый элемент в цепочке
        while (curr != NULL) {
            cache_node_t *next = curr->next; // Следующий элемент
            proxy_log("Delete entry: %s", curr->entry->request);
            cache_node_destroy(curr); // Уничтожение текущего узла
            curr = next; // Переход к следующему узлу
        }
    }
    free(cache->array);
    free(cache);
}

/**
 * @brief Вычисляет хэш для HTTP-запроса
 * @param request      Текст HTTP-запроса
 * @param request_len  Длина запроса в байтах
 * @param size         Размер хэш-таблицы (для получения индекса в массиве)
 * @return Индекс в хэш-таблице (от 0 до size-1)
 * @details Использует простую хэш-функцию: сумма байтов по модулю size
 */
static int hash(const char *request, size_t request_len, int size) {
    if (request == NULL) return 0;
    int hash_value = 0; // Начальное значение хэша = 0
    for (size_t i = 0; i < request_len; i++) { // Проход по всем байтам запроса
        hash_value = (hash_value * 31 + request[i]) % size; // Вычисление нового значения хэша
    }
    return hash_value;
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
    cache_node_t *node = malloc(sizeof(cache_node_t)); // Выделение памяти для узла
    if (node == NULL) {
        if (errno == ENOMEM) proxy_log("Cache node creation error: %s", strerror(errno));
        else proxy_log("Cache node creation error: failed to reallocate memory");
        return NULL;
    }
    node->entry = entry; // Указатель на элемент
    gettimeofday(&node->last_modified_time, 0); // Инициализация времени последнего изменения
    pthread_rwlock_init(&node->rwlock, NULL); // Инициализация rwlock
    node->next = NULL; // Указатель на следующий узел
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
    cache_entry_destroy(node->entry); // Освобождение элемента
    pthread_rwlock_destroy(&node->rwlock); // Уничтожение rwlock
    free(node);
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
    while (cache->garbage_collector_running) {
        usleep(MIN(1000 * cache->entry_expired_time_ms / 2, 1000000)); // Проверяем элементы в 2 раза чаще чем время их жизни
        proxy_log("Garbage collector running");
        gettimeofday(&curr_time, 0);
        for (int i = 0; i < cache->capacity; i++) { // Проход по всем индексам
            cache_node_t *curr = cache->array[i]; // Первый элемент в цепочке
            if (curr == NULL) continue;
            pthread_rwlock_rdlock(&curr->rwlock); // Блокировка rwlock
            cache_node_t *next = NULL; // Указатель на следующий узел
            while (curr != NULL) {
                time_t diff = (curr_time.tv_sec - curr->last_modified_time.tv_sec) * 1000 +
                        (curr_time.tv_usec - curr->last_modified_time.tv_usec) / 1000; // Вычисление времени, прошедшего с последнего доступа
                if (diff >= cache->entry_expired_time_ms) { // Проверка истекло ли время жизни элемента
                    pthread_rwlock_rdlock(&curr->rwlock);
                    next = curr->next; // Получение следующего элемента
                    char *request = curr->entry->request; // Получение запроса
                    size_t request_len = curr->entry->request_len;
                    pthread_rwlock_unlock(&curr->rwlock);
                    cache_delete(cache, request, request_len); // Удаление элемента
                } else {
                    pthread_rwlock_rdlock(&curr->rwlock);
                    next = curr->next; // Получение следующего элемента, если элемент не устарел
                    pthread_rwlock_unlock(&curr->rwlock);
                }
                curr = next;
            }
        }
    }
    proxy_log("Cache garbage collector destroy");
    pthread_exit(NULL);
}

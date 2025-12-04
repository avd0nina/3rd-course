#ifndef CACHE_PROXY_CACHE_H
#define CACHE_PROXY_CACHE_H

#include <pthread.h>
#include <stdatomic.h>

#include "message.h"

#define SUCCESS     0
#define ERROR       (-1)
#define NOT_FOUND   (-2)

/**
 * @brief Элемент кэша, хранящий информацию об HTTP-запросе и ответе
 */
struct cache_entry_t {
    char *request; // текст HTTP-запроса
    size_t request_len; // длина запроса в байтах
    message_t *response; // структура с HTTP-ответом
    atomic_int finished; // атомарный флаг, указывающий, что ответ полностью получен
    pthread_mutex_t mutex; // мьютекс
    pthread_cond_t ready_cond; // условная переменная
    atomic_int deleted; // атомарный флаг, указывающий, что элемент удален из кэша
};
typedef struct cache_entry_t cache_entry_t;

/**
 * @brief Создает новый элемент кэша
 * @param request      Текст HTTP-запроса
 * @param request_len  Длина запроса
 * @param response     Начальный HTTP-ответ (может быть NULL)
 * @return Указатель на созданный элемент или NULL при ошибке
 */
cache_entry_t *cache_entry_create(const char *request, size_t request_len, const message_t *response);

/**
 * @brief Уничтожает элемент кэша, освобождая все ресурсы
 * @param entry Элемент для удаления
 */
void cache_entry_destroy(cache_entry_t *entry);

/**
 * @brief Структура, представляющая кэш в целом
 * @details Реализация скрыта в .c файле для инкапсуляции
 */
struct cache_t;
typedef struct cache_t cache_t;

/**
 * @brief Создает новый кэш с указанными параметрами
 * @param capacity              Максимальное количество элементов
 * @param cache_expired_time_ms Время жизни элемента в миллисекундах
 * @return Указатель на созданный кэш или NULL при ошибке
 */
cache_t *cache_create(int capacity, time_t cache_expired_time_ms);

/**
 * @brief Ищет элемент кэша по запросу
 * @details Если элемент найден но еще загружается, блокирует поток до готовности
 * @param cache        Кэш для поиска
 * @param request      Текст запроса для поиска
 * @param request_len  Длина запроса
 * @return Указатель на найденный элемент или NULL если не найден
 */
cache_entry_t *cache_get(cache_t *cache, const char *request, size_t request_len);

/**
 * @brief Добавляет новый элемент в кэш
 * @param cache Кэш для добавления
 * @param entry Элемент для добавления
 * @return SUCCESS при успешном добавлении, ERROR при ошибке
 */
int cache_add(cache_t *cache, cache_entry_t *entry);

/**
 * @brief Удаляет элемент из кэша по запросу
 * @param cache        Кэш для удаления
 * @param request      Текст запроса для удаления
 * @param request_len  Длина запроса
 * @return SUCCESS при успешном удалении, ERROR или NOT_FOUND при ошибке
 */
int cache_delete(cache_t *cache, const char *request, size_t request_len);

/**
 * @brief Полностью уничтожает кэш, освобождая все ресурсы
 * @param cache Кэш для уничтожения
 */
void cache_destroy(cache_t *cache);

#endif // CACHE_PROXY_CACHE_H

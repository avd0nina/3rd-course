#include "env.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "log.h"

/**
 * @brief Значение по умолчанию для количества потоков-обработчиков
 * @details Используется если переменная окружения CACHE_PROXY_THREAD_POOL_SIZE
 */
#define HANDLER_COUNT_DEFAULT           1

/**
 * @brief Значение по умолчанию для времени жизни элемента кэша (в миллисекундах)
 * @details Используется если переменная окружения CACHE_PROXY_CACHE_EXPIRED_TIME_MS
 */
#define CACHE_EXPIRED_TIME_MS_DEFAULT   (24 * 60 * 60 * 1000)

/**
 * @brief Получает количество потоков-обработчиков из переменной окружения
 * @return Количество потоков-обработчиков для пула потоков прокси
 * @details Алгоритм работы:
 *          1. Пытается прочитать значение переменной CACHE_PROXY_THREAD_POOL_SIZE
 *          2. Если переменная не установлена, возвращает значение по умолчанию (1)
 *          3. Преобразует строковое значение в целое число
 *          4. Проверяет корректность преобразования
 *          5. В случае ошибок возвращает значение по умолчанию с логированием
 */
int env_get_client_handler_count() {
    char *handler_count_env = getenv("CACHE_PROXY_THREAD_POOL_SIZE");
    if (handler_count_env == NULL) {
        proxy_log("CACHE_PROXY_THREAD_POOL_SIZE getting error: variable not set");
        return HANDLER_COUNT_DEFAULT;
    }
    errno = 0;
    char *end;
    int handler_count = (int) strtol(handler_count_env, &end, 0); // Преобразование строки в целое число
    if (errno != 0) {
        proxy_log("CACHE_PROXY_THREAD_POOL_SIZE getting error: %s", strerror(errno));
        return HANDLER_COUNT_DEFAULT;
    }
    if (end == handler_count_env) {
        proxy_log("CACHE_PROXY_THREAD_POOL_SIZE getting error: no digits were found");
        return HANDLER_COUNT_DEFAULT;
    }
    return handler_count;
}

/**
 * @brief Получает время жизни элементов кэша из переменной окружения
 * @return Время жизни элемента кэша в миллисекундах
 * @details Алгоритм работы:
 *          1. Пытается прочитать значение переменной CACHE_PROXY_CACHE_EXPIRED_TIME_MS
 *          2. Если переменная не установлена, возвращает значение по умолчанию (24 часа)
 *          3. Преобразует строковое значение в число типа time_t
 *          4. Проверяет корректность преобразования
 *          5. В случае ошибок возвращает значение по умолчанию с логированием
 */
time_t env_get_cache_expired_time_ms() {
    char *cache_expired_time_ms_env = getenv("CACHE_PROXY_CACHE_EXPIRED_TIME_MS");
    if (cache_expired_time_ms_env == NULL) {
        proxy_log("CACHE_PROXY_CACHE_EXPIRED_TIME_MS getting error: variable not set");
        return CACHE_EXPIRED_TIME_MS_DEFAULT;
    }
    // Convert string to time_t
    errno = 0;
    char *end;
    time_t cache_expired_time_ms = strtol(cache_expired_time_ms_env, &end, 0);
    if (errno != 0) {
        proxy_log("CACHE_PROXY_CACHE_EXPIRED_TIME_MS getting error: %s", strerror(errno));
        return CACHE_EXPIRED_TIME_MS_DEFAULT;
    }
    if (end == cache_expired_time_ms_env) {
        proxy_log("CACHE_PROXY_CACHE_EXPIRED_TIME_MS getting error: no digits were found");
        return CACHE_EXPIRED_TIME_MS_DEFAULT;
    }
    return cache_expired_time_ms;
}

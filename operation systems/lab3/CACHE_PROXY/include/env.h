#ifndef CACHE_PROXY_ENV_H
#define CACHE_PROXY_ENV_H

#include <time.h>

/**
 * @brief Получает количество обработчиков клиентов из переменных окружения
 * @details Читает значение из переменной окружения CLIENT_HANDLER_COUNT
 * @return Количество обработчиков клиентов (по умолчанию 10)
 */
int env_get_client_handler_count();

/**
 * @brief Получает время жизни кэша из переменных окружения
 * @details Читает значение из переменной окружения CACHE_EXPIRED_TIME_MS
 * @return Время жизни элемента кэша в миллисекундах (по умолчанию 60000)
 */
time_t env_get_cache_expired_time_ms();

#endif // CACHE_PROXY_ENV_H

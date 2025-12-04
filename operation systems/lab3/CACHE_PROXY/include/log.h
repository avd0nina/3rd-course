#ifndef CACHE_PROXY_LOG_H
#define CACHE_PROXY_LOG_H

/**
 * @brief Выводит лог-сообщение с форматированием в стандартный поток ошибок (stderr)
 *      с добавлением временной метки и префикса.
 * @param format Строка формата в стиле printf
 * @param ... Аргументы для подстановки в строку формата
 */
void proxy_log(const char* format, ...);

#endif // CACHE_PROXY_LOG_H

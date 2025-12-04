#include "log.h"

#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/time.h>

#define MAX_LOG_MESSAGE_LENGTH  1024

/**
 * @brief Выводит форматированное лог-сообщение с метаданными
 * @param format Строка формата (аналогично printf)
 * @param ... Аргументы для подстановки в строку формата
 * @details Формат вывода:
 *          ГГГГ-ММ-ДД ЧЧ:ММ:СС.ммм --- [имя_потока] : сообщение
 */
void proxy_log(const char *format, ...) {
    struct timeval tv; // Объявление структуры для времени с микросекундной точностью
    gettimeofday(&tv, NULL); // Получение текущего времени с микросекундной точностью
    time_t stamp_time = time(NULL); // Получение текущего времени в секундах
    struct tm *tm = localtime(&stamp_time); // Преобразование времени в локальное (с учетом часового пояса)
    char text[MAX_LOG_MESSAGE_LENGTH + 1];
    va_list args;
    va_start(args, format); // Работа с переменными аргументами
    vsnprintf(text, MAX_LOG_MESSAGE_LENGTH, format, args); // Форматирование
    va_end(args);
    char thread_name[256] = {0};
    pthread_getname_np(pthread_self(), thread_name, sizeof(thread_name)); // Получение имени потока
    printf("%04d-%02d-%02d %02d:%02d:%02d.%03d --- [%15s] : %s\n",
           tm->tm_year + 1900,
           tm->tm_mon + 1,
           tm->tm_mday,
           tm->tm_hour,
           tm->tm_min,
           tm->tm_sec,
           (int)(tv.tv_usec / 1000),
           thread_name,
           text);
    fflush(stdout);
}

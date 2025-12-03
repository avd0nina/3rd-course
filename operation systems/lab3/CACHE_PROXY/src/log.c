#include "log.h"

#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#define MAX_LOG_MESSAGE_LENGTH  1024

void proxy_log(const char *format, ...) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    time_t stamp_time = time(NULL);
    struct tm *tm = localtime(&stamp_time);
    char text[MAX_LOG_MESSAGE_LENGTH + 1];
    va_list args;
    va_start(args, format);
    vsnprintf(text, MAX_LOG_MESSAGE_LENGTH, format, args);
    va_end(args);
    char thread_name[256] = {0};
    pthread_getname_np(pthread_self(), thread_name, sizeof(thread_name));
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

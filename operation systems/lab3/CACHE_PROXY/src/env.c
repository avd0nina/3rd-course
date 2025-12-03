#include "env.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "log.h"

#define HANDLER_COUNT_DEFAULT           1
#define CACHE_EXPIRED_TIME_MS_DEFAULT   (24 * 60 * 60 * 1000)

int env_get_client_handler_count() {
    char *handler_count_env = getenv("CACHE_PROXY_THREAD_POOL_SIZE");
    if (handler_count_env == NULL) {
        proxy_log("CACHE_PROXY_THREAD_POOL_SIZE getting error: variable not set");
        return HANDLER_COUNT_DEFAULT;
    }
    // Convert string to int
    errno = 0;
    char *end;
    int handler_count = (int) strtol(handler_count_env, &end, 0);
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

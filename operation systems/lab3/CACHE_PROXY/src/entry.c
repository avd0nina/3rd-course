#include "cache.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "log.h"

cache_entry_t *cache_entry_create(const char *request, size_t request_len, const message_t *response) {
    errno = 0;
    cache_entry_t *entry = malloc(sizeof(cache_entry_t));
    if (entry == NULL) {
        if (errno == ENOMEM) proxy_log("Cache entry creation error: %s", strerror(errno));
        else proxy_log("Cache entry creation error: failed to reallocate memory");
        return NULL;
    }
    entry->request = (char *) request;
    entry->request_len = request_len;
    entry->response = (message_t *) response;
    pthread_mutex_init(&entry->mutex, NULL);
    pthread_cond_init(&entry->ready_cond, NULL);
    entry->deleted = 0;
    entry->finished = 0;
    return entry;
}

void cache_entry_destroy(cache_entry_t *entry) {
    if (entry == NULL) {
        proxy_log("Cache entry destroying error: entry is NULL");
        return;
    }
    if (entry->request != NULL) free(entry->request);
    if (entry->response != NULL) message_destroy(&entry->response);
    pthread_mutex_destroy(&entry->mutex);
    pthread_cond_destroy(&entry->ready_cond);
    free(entry);
}

#include "cache.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "log.h"

/**
 * @brief Создает новый элемент кэша
 * @param request Текст HTTP-запроса
 * @param request_len Длина запроса в байтах
 * @param response Структура с HTTP-ответом (может быть NULL)
 * @return Указатель на созданный элемент или NULL при ошибке
 * @details Алгоритм работы:
 *          1. Выделяет память под структуру cache_entry_t
 *          2. Копирует указатели на данные запроса и ответа
 *          3. Инициализирует мьютекс и условную переменную для синхронизации
 *          4. Устанавливает начальные значения флагов
 */
cache_entry_t *cache_entry_create(const char *request, size_t request_len, const message_t *response) {
    errno = 0;
    cache_entry_t *entry = malloc(sizeof(cache_entry_t)); // Выделение памяти под элемент кэша
    if (entry == NULL) {
        if (errno == ENOMEM) proxy_log("Cache entry creation error: %s", strerror(errno));
        else proxy_log("Cache entry creation error: failed to reallocate memory");
        return NULL;
    }
    entry->request = (char *) request;
    entry->request_len = request_len;
    entry->response = (message_t *) response;
    pthread_mutex_init(&entry->mutex, NULL); // Инициализация мьютекса
    pthread_cond_init(&entry->ready_cond, NULL); // Инициализирует условную переменную для уведомления потоков
    entry->deleted = 0;
    entry->finished = 0;
    return entry;
}

/**
 * @brief Уничтожает элемент кэша, освобождая все связанные ресурсы
 * @param entry Указатель на элемент кэша для уничтожения
 * @details Выполняет полное освобождение ресурсов элемента кэша:
 *          1. Освобождает память запроса (если не NULL)
 *          2. Уничтожает структуру ответа (если не NULL)
 *          3. Уничтожает мьютекс и условную переменную
 *          4. Освобождает память самой структуры
 */
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

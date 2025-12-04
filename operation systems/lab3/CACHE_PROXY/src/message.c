#include "message.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "log.h"

/**
 * @brief Добавляет новую часть в конец связанного списка сообщений
 * @param message Указатель на указатель на начало списка сообщений
 * @param part    Данные для добавления (будут скопированы)
 * @param part_len Длина данных в байтах
 * @return SUCCESS (0) при успешном добавлении, ERROR (-1) при ошибке
 * @details Алгоритм:
 *          1. Проверяет корректность указателя message
 *          2. Выделяет память для нового узла списка
 *          3. Выделяет память для копии данных part
 *          4. Копирует данные из part в выделенную память
 *          5. Добавляет узел в конец списка
 */
int message_add_part(message_t **message, char *part, size_t part_len) {
    if (message == NULL) {
        proxy_log("Message part adding error: message pointer is NULL");
        return ERROR;
    }
    errno = 0;
    message_t *part_msg = malloc(sizeof(message_t)); // Выделяет память для структуры message_t
    if (part_msg == NULL) {
        if (errno == ENOMEM) proxy_log("Message part adding error: %s", strerror(errno));
        else proxy_log("Message part adding error: failed to reallocate memory");
        return ERROR;
    }
    errno = 0;
    part_msg->part = calloc(sizeof(char), part_len); // Выделение памяти для данных части сообщения
    if (part_msg->part == NULL) {
        if (errno == ENOMEM) proxy_log("Message part adding error: %s", strerror(errno));
        else proxy_log("Message part adding error: failed to reallocate memory");
        free(part_msg);
        return ERROR;
    }
    strncpy(part_msg->part, part, part_len); // Копирование данных в выделенную память
    part_msg->part_len = part_len;
    part_msg->next = NULL;
    if (*message == NULL) { // Добавление узла в пустой список
        *message = part_msg;
        return SUCCESS;
    }
    message_t *end = *message;
    while (end->next != NULL) end = end->next; // Цикл поиска последнего элемента. Перемещается по списку пока не найдет элемент с next == NULL.
    end->next = part_msg; // Добавление узла в конец списка
    return SUCCESS;
}

/**
 * @brief Полностью уничтожает связанный список сообщений
 * @param message Указатель на указатель на начало списка сообщений
 * @details Освобождает всю память, связанную со списком:
 *          1. Память данных каждой части (part)
 *          2. Память узлов списка (message_t)
 *          3. Устанавливает *message = NULL
 */
void message_destroy(message_t **message) {
    if (*message == NULL) return;
    message_t *curr = *message, *tmp = NULL; // curr: указатель на текущий элемент (начинает с головы); tmp: указатель на элемент для освобождения
    while (curr != NULL) {
        tmp = curr;
        curr = curr->next;
        free(tmp->part);
        free(tmp);
    }
    *message = NULL;
}

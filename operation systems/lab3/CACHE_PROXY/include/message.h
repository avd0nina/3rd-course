#ifndef CACHE_PROXY_MESSAGE_H
#define CACHE_PROXY_MESSAGE_H

#include <stddef.h>

#define SUCCESS 0
#define ERROR   (-1)

/**
 * @brief Элемент связанного списка, представляющий часть HTTP-сообщения
 * @details Используется для хранения фрагментов HTTP-ответов, которые
 *          могут приходить частями при потоковой передаче.
 * @var part      Указатель на данные части сообщения
 * @var part_len  Длина части в байтах
 * @var next      Указатель на следующую часть сообщения (NULL если это последняя часть)
 */
struct message_t {
    char *part;
    size_t part_len;
    struct message_t *next;
};
typedef struct message_t message_t;

/**
 * @brief Добавляет новую часть в конец связанного списка сообщений и добавляет его в конец
 * @param message Указатель на указатель на начало списка сообщений
 * @param part    Данные для добавления (копируются внутрь структуры)
 * @param part_len Длина данных в байтах
 * @return SUCCESS при успешном добавлении, ERROR при ошибке выделения памяти
 */
int message_add_part(message_t **message, char *part, size_t part_len);

/**
 * @brief Полностью уничтожает связанный список сообщений
 * @param message Указатель на указатель на начало списка сообщений.
 *                После вызова *message будет установлен в NULL
 */
void message_destroy(message_t **message);

#endif // CACHE_PROXY_MESSAGE_H

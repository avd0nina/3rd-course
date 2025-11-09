#ifndef QUEUE_H
#define QUEUE_H

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "spinlock.h"

#define MAX_STRING_LENGTH 100

/**
 * Узел односвязного списка.
 * Содержит строку, указатель на следующий узел и спинлок для защиты доступа.
 */
typedef struct _Node {
    char value[MAX_STRING_LENGTH];
    struct _Node *next;
    custom_spinlock_t sync;
} Node;

/**
 * Структура хранилища (список).
 * Содержит указатель на голову, ёмкость и мьютекс для защиты головы.
 */
typedef struct _Storage {
    Node *first;
    int capacity;
    pthread_mutex_t head_mutex;
} Storage;

/**Данные, передаваемые в потоки.
 * Используется для передачи общего списка, счётчика и ID потока.
 */
typedef struct _ThreadData {
    Storage *storage;
    int *counter;
    int thread_id;
} ThreadData;

/**
 * Глобальные счётчики пар (защищены global_mutex).
 */
extern int asc_pairs;     ///< Количество пар по возрастанию
extern int desc_pairs;    ///< Количество пар по убыванию
extern int eq_pairs;      ///< Количество пар с равной длиной
extern int swap_counts[3];///< Счётчики успешных перестановок для 3 swap-потоков
extern pthread_mutex_t global_mutex; ///< Мьютекс для защиты счётчиков

/**
 * Создаёт и инициализирует хранилище.
 * @param capacity Количество элементов в списке.
 * @return Указатель на созданное хранилище.
 */
Storage* initialize_storage(int capacity);

/**
 * Добавляет узел в конец списка.
 * @param storage Указатель на хранилище.
 * @param value Строка для копирования.
 */
void add_node(Storage *storage, const char *value);

/**
 * Заполняет список capacity узлами.
 * @param storage Указатель на хранилище.
 * @param capacity Количество узлов.
 */
void fill_storage(Storage *storage, int capacity);

/**
 * Печатает первые 20 узлов списка.
 * @param storage Указатель на хранилище.
 */
void print_storage(Storage *storage);

/**
 * Освобождает всю память, занятую списком.
 * @param storage Указатель на хранилище.
 */
void free_storage(Storage *storage);

/**
 * Возвращает длину списка (с hand-over-hand locking).
 * @param storage Указатель на хранилище.
 * @return Количество узлов.
 */
int get_list_length(Storage *storage);

#endif

#ifndef MUTEX_H
#define MUTEX_H

#include <pthread.h>
#include <stdint.h>

/**
 * Структура пользовательского мьютекса (non-recursive).
 * Содержит только атомарный флаг блокировки.
 */
typedef struct {
    volatile int lock;   /**< Флаг блокировки: 0 = свободен, 1 = занят */
} custom_mutex_t;

/**
 * Инициализирует мьютекс в свободное состояние.
 * @param mutex Указатель на структуру мьютекса.
 */
void custom_mutex_init(custom_mutex_t *mutex);

/**
 * Захватывает мьютекс (блокирующая операция).
 * @param mutex Указатель на мьютекс.
 * @return 0 при успехе
 */
int custom_mutex_lock(custom_mutex_t *mutex);

/**
 * Освобождает мьютекс.
 * @param mutex Указатель на мьютекс.
 * @return 0 при успехе
 */
int custom_mutex_unlock(custom_mutex_t *mutex);

/**
 * Уничтожает мьютекс.
 * @param mutex Указатель на мьютекс.
 */
void custom_mutex_destroy(custom_mutex_t *mutex);

#endif // MUTEX_H

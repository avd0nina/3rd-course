#ifndef MUTEX_H
#define MUTEX_H

#include <pthread.h>
#include <stdint.h>

/**
 * Структура пользовательского рекурсивного мьютекса.
 * Содержит атомарный флаг блокировки, идентификатор владельца и счётчик вложенных захватов для поддержки рекурсии.
 */
typedef struct {
    volatile int lock;   /**< Флаг блокировки: 0 = свободен, 1 = занят */
    pthread_t owner;     /**< ID потока-владельца (для рекурсии) */
    int count;           /**< Счётчик рекурсивных захватов */
} custom_mutex_t;

/**
 * Инициализирует мьютекс в свободное состояние.
 * @param mutex Указатель на структуру мьютекса.
 */
void custom_mutex_init(custom_mutex_t *mutex);

/**
 * Захватывает мьютекс (блокирующая операция).
 * @param mutex Указатель на мьютекс.
 * @return
 *   - `0` - мьютекс успешно захвачен
 *   - Ненулевое значение — ошибка (например, deadlock или повреждение)
 */
int custom_mutex_lock(custom_mutex_t *mutex);

/**
 * Освобождает мьютекс.
 * @param mutex Указатель на мьютекс.
 * @return
 *   - `0` - мьютекс успешно освобождён
 *   - Ненулевое значение — ошибка (например, не владелец)
 */
int custom_mutex_unlock(custom_mutex_t *mutex);

/**
 * Уничтожает мьютекс.
 * В текущей реализации ничего не делает - структура статическая. Оставлена для совместимости с `pthread_mutex_destroy`.
 * @param mutex Указатель на мьютекс.
 */
void custom_mutex_destroy(custom_mutex_t *mutex);

#endif // MUTEX_H

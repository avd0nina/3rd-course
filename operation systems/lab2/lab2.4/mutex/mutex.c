#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include "mutex.h"

/**
 * Вспомогательная функция для вызова системного вызова futex.
 * Обёртка над `syscall(SYS_futex, ...)`. Используется для:
 * - FUTEX_WAIT - усыпить поток
 * - FUTEX_WAKE - разбудить ожидающий поток
 * @param uaddr    Указатель на атомарную переменную (в нашем случае — &mutex->lock)
 * @param op       Операция: FUTEX_WAIT или FUTEX_WAKE
 * @param val      Ожидаемое значение для WAIT, количество потоков для WAKE
 * @param timeout  Таймаут (NULL — бесконечно)
 * @return Результат системного вызова (0 при успехе, -1 при ошибке)
 */
static int futex(int *uaddr, int op, int val, const struct timespec *timeout) {
    return syscall(SYS_futex, uaddr, op, val, timeout, NULL, 0);
}

/**
 * Инициализирует мьютекс в свободное состояние.
 * Устанавливает начальные значения:
 * - `lock = 0` - мьютекс свободен
 * @param mutex Указатель на структуру мьютекса.
 */
void custom_mutex_init(custom_mutex_t *mutex) {
    mutex->lock = 0;
}

/**
 * Захватывает мьютекс (блокирующая операция).
 * futex WAIT при невозможности захватить
 */
int custom_mutex_lock(custom_mutex_t *mutex) {
    // Пока не удастся захватить — усыпляемся в ядре
    while (!__sync_bool_compare_and_swap(&mutex->lock, 0, 1)) {
        // Усыпляем поток только если мьютекс всё ещё занят (lock == 1)
        if (mutex->lock == 1) {
            int ret = futex((int*)&mutex->lock, FUTEX_WAIT, 1, NULL);
            // EAGAIN - нормальная ситуация (мьютекс изменился перед вызовом WAIT)
            if (ret == -1 && errno != EAGAIN) {
                // В реальном коде здесь должна быть обработка ошибок
                perror("futex wait failed");
            }
        }
    }
    return 0;
}

/**
 * Освобождает мьютекс.
 * Атомарно сбрасывает lock в 0 и будит один ожидающий поток.
 */
int custom_mutex_unlock(custom_mutex_t *mutex) {
    // Атомарно освобождаем мьютекс
    __atomic_store_n(&mutex->lock, 0, __ATOMIC_RELEASE);
    // Будим один ожидающий поток
    futex((int*)&mutex->lock, FUTEX_WAKE, 1, NULL);
    return 0;
}

/**
 * Уничтожает мьютекс.
 * В текущей реализации ничего не делает — структура статическая.
 * Оставлена для совместимости с `pthread_mutex_destroy`.
 * @param mutex Указатель на мьютекс.
 */
void custom_mutex_destroy(custom_mutex_t *mutex) {
    (void)mutex;
}

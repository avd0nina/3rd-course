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
 * @param uaddr2   Не используется (NULL)
 * @param val3     Не используется (0)
 * @return Результат системного вызова (0 при успехе, -1 при ошибке)
 */
static inline int futex(int *uaddr, int op, int val, const struct timespec *timeout,
                        int *uaddr2, int val3) {
    return syscall(SYS_futex, uaddr, op, val, timeout, uaddr2, val3);
}

/**
 * Инициализирует мьютекс в свободное состояние.
 * Устанавливает начальные значения:
 * - `lock = 0` - мьютекс свободен
 * - `owner = 0` - нет владельца
 * - `count = 0` - нет захватов
 * @param mutex Указатель на структуру мьютекса.
 */
void custom_mutex_init(custom_mutex_t *mutex) {
    mutex->lock = 0;
    mutex->owner = 0;
    mutex->count = 0;
}

/**
 * Захватывает мьютекс (блокирующая операция).
 * Алгоритм:
 * 1. Рекурсия: если текущий поток - владелец → увеличиваем count.
 * 2. Быстрый путь (userspace): 100 попыток CAS (`__sync_bool_compare_and_swap`).
 *    - Успех → устанавливаем owner, count = 1, выходим.
 *    - Неудача → `__builtin_ia32_pause()` (снижает нагрузку на CPU).
 * 3. Медленный путь (kernel): если CAS не удался - вызываем `futex_wait`.
 *    - Поток усыпляется в ядре, пока другой поток не вызовет `futex_wake`.
 * @param mutex Указатель на мьютекс.
 * @return
 *   - `0` - мьютекс захвачен
 */
int custom_mutex_lock(custom_mutex_t *mutex) {
    pthread_t self = pthread_self();
    // РЕКУРСИЯ: если мы уже владелец - просто увеличиваем счётчик
    if (pthread_equal(mutex->owner, self)) {
        mutex->count++;
        return 0;
    }
    // БЫСТРЫЙ ПУТЬ: спин с CAS (100 попыток)
    for (int i = 0; i < 100; i++) {
        int expected = 0;
        if (__sync_bool_compare_and_swap(&mutex->lock, expected, 1)) {
            // Успешно захватили: устанавливаем владельца и счётчик
            mutex->owner = self;
            mutex->count = 1;
            return 0;
        }
        __builtin_ia32_pause();  // Снижаем нагрузку на CPU
    }
    // МЕДЛЕННЫЙ ПУТЬ: переходим к futex
    // Пока не удастся захватить — усыпляемся
    while (!__sync_bool_compare_and_swap(&mutex->lock, 0, 1)) {
        if (mutex->lock == 1) {
            // Только если lock == 1 - усыпляемся
            int ret = futex((int*)&mutex->lock, FUTEX_WAIT, 1, NULL, NULL, 0);
            if (ret == -1 && errno != EAGAIN) {
            }
        }
    }
    // Успешно захватили после пробуждения
    mutex->owner = self;
    mutex->count = 1;
    return 0;
}

/**
 * Освобождает мьютекс.
 * Поведение:
 * - Если count > 1 - уменьшаем счётчик, мьютекс остаётся захваченным.
 * - Если count == 1:
 *   - Сбрасываем owner
 *   - Атомарно устанавливаем lock = 0
 *   - Вызываем `futex_wake(1)` — будим один ожидающий поток
 * @param mutex Указатель на мьютекс.
 * @return
 *   - `0` — мьютекс освобождён
 *   - `1` — ошибка (не владелец или count <= 0)
 */
int custom_mutex_unlock(custom_mutex_t *mutex) {
    // Проверка: только владелец может разблокировать
    if (!pthread_equal(mutex->owner, pthread_self()) || mutex->count <= 0) {
        fprintf(stderr, "Unlock error: not owner or count <= 0\n");
        return 1;
    }
    mutex->count--;
    // Только при полном освобождении — сбрасываем lock и будим
    if (mutex->count == 0) {
        mutex->owner = 0;
        __atomic_store_n(&mutex->lock, 0, __ATOMIC_RELEASE);
        futex((int*)&mutex->lock, FUTEX_WAKE, 1, NULL, NULL, 0);
    }
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

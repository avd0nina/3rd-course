#include "spinlock.h"
#include <unistd.h>

/**
 * Инициализирует пользовательский спинлок в свободное состояние.
 * Устанавливает внутренний флаг блокировки в 0, что означает, что спинлок свободен и готов к использованию.
 * @param lock Указатель на структуру custom_spinlock_t.
 */
void custom_spin_init(custom_spinlock_t *lock) {
    lock->lock = 0;
}

/**
 * Атомарно захватывает спинлок с активным ожиданием.
 * Поток блокируется в цикле, пока не удастся атомарно установить значение флага в 1. Используется инструкция PAUSE для снижения
 * нагрузки на процессор и предотвращения livelock.
 * @param lock Указатель на структуру custom_spinlock_t.
 */
void custom_spin_lock(custom_spinlock_t *lock) {
    while (!__sync_bool_compare_and_swap(&lock->lock, 0, 1)) {
        __builtin_ia32_pause(); 
    }
}

/**
 * Освобождает спинлок с release-барьером.
 * Атомарно сбрасывает флаг блокировки в 0. __ATOMIC_RELEASE гарантирует, что все изменения в критической
 * секции видны другим потокам до момента разблокировки.
 * @param lock Указатель на структуру custom_spinlock_t.
 */
void custom_spin_unlock(custom_spinlock_t *lock) {
    __atomic_store_n(&lock->lock, 0, __ATOMIC_RELEASE);
}

/**
 * Уничтожение спинлока.
 * Для данной реализации спинлока ничего не требуется - структура статическая. Функция оставлена для единообразия с другими
 * примитивами синхронизации.
 */
void custom_spin_destroy(custom_spinlock_t *lock) {
    (void)lock;
}

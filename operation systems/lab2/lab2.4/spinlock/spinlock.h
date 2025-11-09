#ifndef SPINLOCK_H
#define SPINLOCK_H

/**
 * Пользовательский спинлок на основе атомарных операций.
 */
typedef struct {
    /** Флаг блокировки: 0 - свободен, 1 - захвачен. */
    volatile int lock;
} custom_spinlock_t;

/**
 * Инициализирует спинлок в свободное состояние.
 */
void custom_spin_init(custom_spinlock_t *lock);

/**
 * Атомарно захватывает спинлок с активным ожиданием.
 */
void custom_spin_lock(custom_spinlock_t *lock);

/**
 * Освобождает спинлок.
 */
void custom_spin_unlock(custom_spinlock_t *lock);

/**
 * Уничтожение спинлока.
 */
void custom_spin_destroy(custom_spinlock_t *lock);

#endif

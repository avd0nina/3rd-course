#include "spinlock.h"
#include <unistd.h>

void custom_spin_init(custom_spinlock_t *lock) {
    lock->lock = 0;
}

void custom_spin_lock(custom_spinlock_t *lock) {
    while (!__sync_bool_compare_and_swap(&lock->lock, 0, 1)) {
        __builtin_ia32_pause(); 
    }
}

void custom_spin_unlock(custom_spinlock_t *lock) {
    __atomic_store_n(&lock->lock, 0, __ATOMIC_RELEASE);
}

void custom_spin_destroy(custom_spinlock_t *lock) {
    (void)lock;
}

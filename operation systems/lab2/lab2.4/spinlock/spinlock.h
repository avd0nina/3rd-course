#ifndef SPINLOCK_H
#define SPINLOCK_H

typedef struct {
    volatile int lock;  
} custom_spinlock_t;

void custom_spin_init(custom_spinlock_t *lock);
void custom_spin_lock(custom_spinlock_t *lock);
void custom_spin_unlock(custom_spinlock_t *lock);
void custom_spin_destroy(custom_spinlock_t *lock);

#endif

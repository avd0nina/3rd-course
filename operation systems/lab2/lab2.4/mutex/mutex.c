#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include "mutex.h"

static inline int futex(int *uaddr, int op, int val, const struct timespec *timeout,
                        int *uaddr2, int val3) {
    return syscall(SYS_futex, uaddr, op, val, timeout, uaddr2, val3);
}

void custom_mutex_init(custom_mutex_t *mutex) {
    mutex->lock = 0;
    mutex->owner = 0;
    mutex->count = 0;
}

int custom_mutex_lock(custom_mutex_t *mutex) {
    pthread_t self = pthread_self();
    if (pthread_equal(mutex->owner, self)) {
        mutex->count++;
        return 0;
    }
    for (int i = 0; i < 100; i++) {
        int expected = 0;
        if (__sync_bool_compare_and_swap(&mutex->lock, expected, 1)) {
            mutex->owner = self;
            mutex->count = 1;
            return 0;
        }
        __builtin_ia32_pause();
    }
    while (!__sync_bool_compare_and_swap(&mutex->lock, 0, 1)) {
        if (mutex->lock == 1) {
            int ret = futex((int*)&mutex->lock, FUTEX_WAIT, 1, NULL, NULL, 0);
            if (ret == -1 && errno != EAGAIN) {
                perror("futex wait");
            }
        }
    }
    mutex->owner = self;
    mutex->count = 1;
    return 0;
}

int custom_mutex_unlock(custom_mutex_t *mutex) {
    if (!pthread_equal(mutex->owner, pthread_self()) || mutex->count <= 0) {
        fprintf(stderr, "Unlock error: not owner or count <= 0\n");
        return 1;
    }
    mutex->count--;
    if (mutex->count == 0) {
        mutex->owner = 0;
        __atomic_store_n(&mutex->lock, 0, __ATOMIC_RELEASE);
        futex((int*)&mutex->lock, FUTEX_WAKE, 1, NULL, NULL, 0);
    }
    return 0;
}

void custom_mutex_destroy(custom_mutex_t *mutex) {
    (void)mutex;
}

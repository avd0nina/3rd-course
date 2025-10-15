#ifndef UTHREAD_H
#define UTHREAD_H

#include <ucontext.h>
#include <pthread.h>

#define MAX_THREADS_COUNT 8

typedef void *(*start_routine_t)(void *);

typedef struct uthread_struct {
    int uthread_id;
    start_routine_t start_routine;
    void *arg;
    void *retval;
    ucontext_t ucontext;
    int state;
    pthread_mutex_t join_mutex;
    pthread_cond_t join_cond;
} uthread_struct_t;

typedef uthread_struct_t *uthread_t;

int uthread_init(void);
int uthread_create(uthread_t *thread, start_routine_t start_routine, void *arg);
int uthread_join(uthread_t thread, void **retval);
void uthread_scheduler(void);
void uthread_cleanup(void);
int create_stack(void **stack, size_t size);

enum { STATE_READY, STATE_RUNNING, STATE_FINISHED };

#endif // UTHREAD_H

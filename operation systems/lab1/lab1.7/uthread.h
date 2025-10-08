#ifndef UTHREAD_H
#define UTHREAD_H

#include <ucontext.h>

#define MAX_THREADS_COUNT 8

typedef void *(*start_routine_t)(void *);

typedef struct uthread_struct {
    int uthread_id;
    start_routine_t start_routine;
    void *arg;
    ucontext_t ucontext;
} uthread_struct_t;

typedef uthread_struct_t *uthread_t;

int uthread_init(void);
int uthread_create(uthread_t *thread, start_routine_t start_routine, void *arg);
int uthread_join(uthread_t thread, void **retval);
void uthread_scheduler(void);
void uthread_cleanup(void); 

#endif // UTHREAD_H

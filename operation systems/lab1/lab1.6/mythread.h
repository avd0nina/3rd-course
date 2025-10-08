#ifndef MYTHREAD_H
#define MYTHREAD_H

typedef void *(*start_routine_t)(void *);

typedef struct {
    int mythread_id;
    start_routine_t start_routine;
    void *arg;
    void *retval;
    volatile int joined;
    volatile int exited;
} mythread_struct_t;

typedef mythread_struct_t *mythread_t;

int mythread_create(mythread_t *thread, start_routine_t start_routine, void *arg);
int mythread_join(mythread_t thread, void **retval);

#endif // MYTHREAD_H

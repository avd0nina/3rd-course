#include "uthread.h"
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/mman.h>
#include <stdlib.h>

#define PAGE 4096
#define STACK_SIZE (PAGE * 8)
#define START 0
#define FINISH 1

static uthread_struct_t *uthreads[MAX_THREADS_COUNT];
static int thread_finished[MAX_THREADS_COUNT];
static int uthread_count = 0;
static int uthread_cur = 0;
static void *stacks[MAX_THREADS_COUNT];

int create_stack(void **stack, size_t size) {
    *stack = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (*stack == MAP_FAILED) {
        fprintf(stderr, "create_stack: failed mmap: %s\n", strerror(errno));
        return -1;
    }
    memset(*stack, 0x7f, size);
    return 0;
}

int uthread_init(void) {
    if (uthread_count != 0) {
        fprintf(stderr, "uthread_init: already initialized\n");
        return -1;
    }
    if (create_stack(&stacks[0], STACK_SIZE) == -1) {
        fprintf(stderr, "uthread_init: failed to create stack\n");
        return -1;
    }
    uthread_struct_t *main_thread = (uthread_struct_t *)((char *)stacks[0] + STACK_SIZE - sizeof(uthread_struct_t));
    if (getcontext(&main_thread->ucontext) == -1) {
        fprintf(stderr, "uthread_init: getcontext failed: %s\n", strerror(errno));
        munmap(stacks[0], STACK_SIZE);
        return -1;
    }
    main_thread->ucontext.uc_stack.ss_sp = stacks[0];
    main_thread->ucontext.uc_stack.ss_size = STACK_SIZE - sizeof(uthread_struct_t);
    main_thread->ucontext.uc_link = NULL;
    main_thread->uthread_id = 0;
    main_thread->start_routine = NULL;
    main_thread->arg = NULL;
    main_thread->retval = NULL;
    uthreads[0] = main_thread;
    thread_finished[0] = START;
    uthread_count = 1;
    return 0;
}

void uthread_cleanup(void) {
    for (int i = 0; i < uthread_count; i++) {
        if (stacks[i] != NULL) {
            if (munmap(stacks[i], STACK_SIZE) == -1) {
                fprintf(stderr, "uthread_cleanup: munmap failed for stack %d: %s\n", i, strerror(errno));
            }
            stacks[i] = NULL;
        }
    }
    uthread_count = 0;
    uthread_cur = 0;
}

void uthread_scheduler(void) {
    if (uthread_count <= 1) return;
    int err;
    ucontext_t *cur_context = &(uthreads[uthread_cur]->ucontext);
    int prev = uthread_cur;
    uthread_cur = (uthread_cur + 1) % uthread_count;
    while (uthread_cur != prev && thread_finished[uthread_cur] == FINISH) {
        uthread_cur = (uthread_cur + 1) % uthread_count;
    }
    if (uthread_cur == prev && thread_finished[prev] == FINISH) {
        return;
    }
    ucontext_t *next_context = &(uthreads[uthread_cur]->ucontext);
    err = swapcontext(cur_context, next_context);
    if (err == -1) {
        fprintf(stderr, "uthread_scheduler: swapcontext failed: %s\n", strerror(errno));
        exit(1);
    }
}

void uthread_startup(void *arg) {
    uthread_struct_t *mythread = (uthread_struct_t *) arg;
    thread_finished[mythread->uthread_id] = START;
    mythread->retval = mythread->start_routine(mythread->arg); // Сохраняем возвращаемое значение
    thread_finished[mythread->uthread_id] = FINISH;
}

int uthread_create(uthread_t *thread, start_routine_t start_routine, void *arg) {
    if (uthread_count == 0) {
        fprintf(stderr, "uthread_create: library not initialized\n");
        return -1;
    }
    if (start_routine == NULL) {
        fprintf(stderr, "uthread_create: start_routine is NULL\n");
        return -1;
    }
    if (uthread_count >= MAX_THREADS_COUNT) {
        fprintf(stderr, "uthread_create: max threads count exceeded\n");
        return -1;
    }
    void *stack;
    int err = create_stack(&stack, STACK_SIZE);
    if (err == -1) {
        fprintf(stderr, "uthread_create: failed to create stack\n");
        return -1;
    }
    stacks[uthread_count] = stack;
    uthread_struct_t *mythread = (uthread_struct_t *)((char *)stack + STACK_SIZE - sizeof(uthread_struct_t));
    err = getcontext(&mythread->ucontext);
    if (err == -1) {
        fprintf(stderr, "uthread_create: getcontext failed: %s\n", strerror(errno));
        munmap(stack, STACK_SIZE);
        return -1;
    }
    mythread->ucontext.uc_stack.ss_sp = stack;
    mythread->ucontext.uc_stack.ss_size = STACK_SIZE - sizeof(uthread_struct_t);
    mythread->ucontext.uc_link = &uthreads[0]->ucontext;
    makecontext(&mythread->ucontext, (void (*)(void)) uthread_startup, 1, mythread);
    mythread->uthread_id = uthread_count;
    mythread->start_routine = start_routine;
    mythread->arg = arg;
    mythread->retval = NULL;
    uthreads[uthread_count] = mythread;
    uthread_count++;
    *thread = mythread;
    return 0;
}

int uthread_join(uthread_t thread, void **retval) {
    if (thread == NULL) {
        fprintf(stderr, "uthread_join: thread is NULL\n");
        return -1;
    }
    while (thread_finished[thread->uthread_id] != FINISH) {
        uthread_scheduler();
    }
    if (retval) {
        *retval = thread->retval; // Возвращаем сохранённое значение
    }
    return 0;
}

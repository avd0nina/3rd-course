#include "mythread.h"
#include <sched.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <stdlib.h>

#define PAGE 4096
#define STACK_SIZE (PAGE * 8)

static int thread_num = 0;

int mythread_startup(void *arg) {
    mythread_struct_t *mythread = (mythread_struct_t *) arg;
    mythread->retval = mythread->start_routine(mythread->arg);
    mythread->exited = 1;
    return 0;
}

int create_stack(void **stack, size_t size) {
    *stack = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (*stack == MAP_FAILED) {
        fprintf(stderr, "create_stack: failed mmap: %s\n", strerror(errno));
        return -1;
    }
    memset(*stack, 0x7f, size);
    return 0;
}

int mythread_create(mythread_t *thread, start_routine_t start_routine, void *arg) {
    if (start_routine == NULL) {
        fprintf(stderr, "mythread_create: start_routine is NULL\n");
        return -1;
    }
    void *child_stack = NULL;
    int err = create_stack(&child_stack, STACK_SIZE);
    if (err == -1) {
        return -1;
    }
    mythread_struct_t *mythread = (mythread_struct_t *)malloc(sizeof(mythread_struct_t));
    if (!mythread) {
        fprintf(stderr, "mythread_create: malloc failed\n");
        munmap(child_stack, STACK_SIZE);
        return -1;
    }
    
    mythread->mythread_id = thread_num++;
    mythread->start_routine = start_routine;
    mythread->arg = arg;
    mythread->joined = 0;
    mythread->exited = 0;
    mythread->retval = NULL;

    void *stack_top = (char *)child_stack + STACK_SIZE;
    stack_top = (void *)((unsigned long)stack_top & ~0xF);
    
    int child_pid = clone(mythread_startup, stack_top, CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD, (void *)mythread);
    if (child_pid == -1) {
        fprintf(stderr, "mythread_create: clone failed: %s\n", strerror(errno));
        free(mythread);
        munmap(child_stack, STACK_SIZE);
        return -1;
    }
    *thread = mythread;
    return 0;
}

int mythread_join(mythread_t thread, void **retval) {
    mythread_struct_t *mythread = thread;
    while (!mythread->exited) {
        usleep(1000);
    }
    if (retval) {
        *retval = mythread->retval;
    }
    mythread->joined = 1;
    free(mythread);
    return 0;
}

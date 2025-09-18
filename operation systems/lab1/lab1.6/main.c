#define _GNU_SOURCE

#include <sched.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <fcntl.h>

#define PAGE 4096
#define STACK_SIZE (PAGE * 8)

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

void *mythread(void *arg) { // рабочий
    printf("thread pid: %d\n", getpid());
    char *str = (char *) arg;
    for (int i = 0; i < 5; ++i) {
        printf("hello: %s\n", str);
        sleep(1);
    }
    return "bye";
}

int mythread_startup(void *arg) { // эту функцию вызывает clone
    mythread_struct_t *mythread = (mythread_struct_t *) arg;
    printf("mythread_startup: starting a thread function for thread %d\n", mythread->mythread_id);
    mythread->retval = mythread->start_routine(mythread->arg); // запускает рабочего
    mythread->exited = 1;
    printf("mythread_startup: waiting join for thread %d\n", mythread->mythread_id);
    while (!mythread->joined) {
        sleep(1);
    }
    printf("mythread_startup: thread function finished for thread %d", mythread->mythread_id);
    return 0;
}

int create_stack(void **stack, off_t size, int thread_num) {
    char stack_file[128];
    int stack_fd;
    snprintf(stack_file, sizeof(stack_file), "stack-%d", thread_num);
    stack_fd = open(stack_file, O_RDWR | O_CREAT, 0660);
    if (stack_fd == -1) {
        printf("create_stack: failed to open file");
        return -1;
    }
    int err = ftruncate(stack_fd, 0);
    if (err == -1) {
        printf("create_stack: failed to ftruncate");
        return -1;
    }
    err = ftruncate(stack_fd, size);
    if (err == -1) {
        printf("create_stack: failed to ftruncate");
        return -1;
    }
    *stack = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_STACK, stack_fd, 0);
    if (*stack == MAP_FAILED) {
        printf("create_stack: failed mmap");
        return -1;
    }
    err = close(stack_fd);
    if (err == -1) {
        printf("create_stack: failed to close");
        return -1;
    }
    memset(*stack, 0x7f, size);
    return 1;
}

int mythread_create(mythread_t *mytid, start_routine_t start_routine, void *arg) {
    static int thread_num = 0;
    printf("mythread_create: creating thread %d\n", thread_num);
    void *child_stack = NULL;
    int err = create_stack(&child_stack, STACK_SIZE, thread_num);
    if (err == -1) {
        printf("mythread_create: failed to create stack");
        return -1;
    }
    mprotect(child_stack + PAGE, STACK_SIZE - PAGE, PROT_READ | PROT_WRITE);
    mythread_struct_t *mythread = (mythread_struct_t *) (child_stack + STACK_SIZE - sizeof(mythread_struct_t));
    mythread->mythread_id = thread_num;
    mythread->start_routine = start_routine;
    mythread->arg = arg;
    mythread->joined = 0;
    mythread->exited = 0;
    mythread->retval = NULL;
    thread_num++;
    child_stack = (void *) mythread;
    printf("mythread_create: child stack %p, mythread_struct %p \n", child_stack, mythread);
    int child_pid = clone(mythread_startup, child_stack,
                          CLONE_VM | CLONE_FILES | CLONE_THREAD | CLONE_SIGHAND | SIGCHLD, (void *) mythread);
    if (child_pid == -1) {
        printf("clone failed: %s \n", strerror(errno));
        return -1;
    }
    *mytid = mythread;
    return 0;
}

int mythread_join(mythread_t mytid, void **retval) {
    mythread_struct_t *mythread = mytid;
    printf("mythread_join: waiting for the thread %d finish\n", mythread->mythread_id);
    while (!mythread->exited) {
        sleep(1);
    }
    printf("mythread_join: the thread %d finish\n", mythread->mythread_id);
    *retval = mythread->retval;
    mythread->joined = 1;
    return 0;
}

int main() {
    mythread_t mytid;
    void *retval;
    printf("main [%d %d %d]: Hello from main!\n", getpid(), getppid(), gettid());
    int err = mythread_create(&mytid, mythread, "Hello from thread");
    if (err == -1) {
        printf("thread create failed\n");
    }
    mythread_join(mytid, &retval);
    printf("main [%d %d %d] thread returned '%s'\n", getpid(), getppid(), gettid(), (char *) retval);
    return 0;
}

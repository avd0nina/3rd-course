#define _GNU_SOURCE
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <ucontext.h>
#include <stdlib.h>

#define PAGE 4096
#define STACK_SIZE (PAGE * 8)
#define MAX_THREADS_COUNT 8
#define START 0
#define FINISH 1

typedef struct {
    int uthread_id;
    void (*start_routine)(void *);
    void *arg;
    ucontext_t ucontext;
} uthread_struct_t;

uthread_struct_t *uthreads[MAX_THREADS_COUNT];
int thread_finished[MAX_THREADS_COUNT];
int uthread_count = 0;
int uthread_cur = 0;

void uthread_scheduler() {
    int err;
    ucontext_t *cur_context, *next_context;
    cur_context = &(uthreads[uthread_cur]->ucontext);
    uthread_cur = (uthread_cur + 1) % uthread_count;
    next_context = &(uthreads[uthread_cur]->ucontext);
    err = swapcontext(cur_context, next_context);
    if (err == -1) {
        printf("Bad swap context");
        exit(1);
    }
}

void mythread_func_1(void *arg) {
    char *str = (char *) arg;
    printf("mythread_func_1 started,arg: %s, pid %d, ppid %d, tid %d\n", str, getpid(), getppid(), gettid());
    for (int i = 0; i < 5; i++) {
        printf("hello in mythread_func_1: %s\n", str);
        sleep(1);
        uthread_scheduler();
    }
    puts("mythread_func_1 finished");
}

void mythread_func_2(void *arg) {
    char *str = (char *) arg;
    printf("mythread_func_2 started,arg: %s, pid %d, ppid %d, tid %d\n", str, getpid(), getppid(), gettid());
    for (int i = 0; i < 5; i++) {
        printf("hello in mythread_func_2: %s\n", str);
        sleep(1);
        uthread_scheduler();
    }
    puts("mythread_func_2 finished");
}

void mythread_func_3(void *arg) {
    char *str = (char *) arg;
    printf("mythread_func_3 started,arg: %s, pid %d, ppid %d, tid %d\n", str, getpid(), getppid(), gettid());
    for (int i = 0; i < 10; i++) {
        printf("hello in mythread_func_3: %s\n", str);
        sleep(1);
        uthread_scheduler();
    }
    puts("mythread_func_3 finished");
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

void uthread_startup(void *arg) {
    uthread_struct_t *mythread = (uthread_struct_t *) arg;
    thread_finished[uthread_cur] = START;
    mythread->start_routine(mythread->arg);
    thread_finished[uthread_cur] = FINISH;
}

int uthread_create(uthread_struct_t **thread, void *(start_routine), void *arg) {
    printf("uthread_create: creating thread %d\n", uthread_count);
    void *stack;
    int err = create_stack(&stack, STACK_SIZE, uthread_count);
    if (err == -1) {
        printf("uthread_create: failed to create stack");
        return -1;
    }
    mprotect(stack + PAGE, STACK_SIZE - PAGE, PROT_READ | PROT_WRITE);
    uthread_struct_t *mythread = (uthread_struct_t *) (stack + STACK_SIZE - sizeof(uthread_struct_t));
    printf("uthread_create: child stack %p, mythread_struct %p \n", stack, mythread);
    err = getcontext(&mythread->ucontext);
    if (err == -1) {
        printf("Bad getcontext in thread %d", uthread_count);
        return -1;
    }
    mythread->ucontext.uc_stack.ss_sp = stack;
    mythread->ucontext.uc_stack.ss_size = STACK_SIZE - sizeof(uthread_struct_t);
    mythread->ucontext.uc_link = &uthreads[0]->ucontext; // uc_link — указатель на следующий контекст. здесь же это возврат к главному потоку. устанавливаем контекст, к которому вернётся управление после завершения потока.
    makecontext(&mythread->ucontext, (void (*)(void)) uthread_startup, 1, mythread); // модифицирует контекст, созданный getcontext, чтобы он выполнял указанную функцию с аргументами
    mythread->uthread_id = uthread_count;
    mythread->start_routine = start_routine;
    mythread->arg = arg;
    uthreads[uthread_count] = mythread;
    uthread_count++;
    *thread = mythread;
    return 1;
}

int main() {
    uthread_struct_t *utid[3];
    uthread_struct_t main_thread;
    uthreads[0] = &main_thread;
    uthread_count = 1;
    printf("main [%d %d %d]: Hello from main!\n", getpid(), getppid(), gettid());
    int err = uthread_create(&utid[0], mythread_func_1, "Arg hello 1");
    if (err == -1) {
        puts("Create 1 failed");
        exit(1);
    }
    err = uthread_create(&utid[1], mythread_func_2, "Arg hello 2");
    if (err == -1) {
        puts("Create 2 failed");
        exit(1);
    }
    err = uthread_create(&utid[2], mythread_func_3, "Arg hello 3");
    if (err == -1) {
        puts("Create 3 failed");
        exit(1);
    }
    while (1) {
        uthread_scheduler();
        int count = 0;
        for (int i = 1; i < uthread_count; i++) {
            if ((thread_finished[i]) == FINISH) {
                count++;
            }
            else{
                break;
            }
        }
        if (count == uthread_count - 1) {
            break;
        }
    }
    puts("main finished");
    return 0;
}

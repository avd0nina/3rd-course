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
#define GUARD_PAGE PAGE

static int thread_num = 0;

/**
 * Функция запуска потока, вызываемая через clone.
 * Выполняет переданную функцию потока и устанавливает флаг завершения.
 * @param arg Указатель на структуру mythread_struct_t
 * @return Всегда 0
 */
int mythread_startup(void *arg) {
    mythread_struct_t *mythread = (mythread_struct_t *) arg;
    mythread->retval = mythread->start_routine(mythread->arg);
    mythread->exited = 1;
    return 0;
}

/**
 * Выделяет память для стека потока с защитной страницей.
 * Использует mmap для выделения памяти и mprotect для создания guard page.
 * @param stack Указатель для хранения адреса стека
 * @param size Размер стека (без учёта защитной страницы)
 * @return 0 при успехе, -1 при ошибке
 */
int create_stack(void **stack, size_t size) {
    size_t total_size = size + GUARD_PAGE;
    *stack = mmap(NULL, total_size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (*stack == MAP_FAILED) {
        fprintf(stderr, "create_stack: failed mmap: %s\n", strerror(errno));
        return -1;
    }
    if (mprotect(*stack, GUARD_PAGE, PROT_NONE) == -1) {
        fprintf(stderr, "create_stack: failed mprotect: %s\n", strerror(errno));
        munmap(*stack, total_size);
        return -1;
    }
    memset((char *)*stack + GUARD_PAGE, 0x7f, size);
    return 0;
}

/**
 * Создаёт новый поток с помощью clone.
 * Выделяет стек и структуру потока, инициализирует метаданные.
 * @param thread Указатель для хранения дескриптора потока
 * @param start_routine Функция, выполняемая в потоке
 * @param arg Аргумент для функции потока
 * @return 0 при успехе, -1 при ошибке
 */
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
        munmap(child_stack, STACK_SIZE + GUARD_PAGE);
        return -1;
    }
    
    mythread->mythread_id = thread_num++;
    mythread->start_routine = start_routine;
    mythread->arg = arg;
    mythread->exited = 0;
    mythread->retval = NULL;
    mythread->stack = child_stack;
    mythread->stack_size = STACK_SIZE + GUARD_PAGE;

    void *stack_top = (char *)child_stack + STACK_SIZE + GUARD_PAGE;
    stack_top = (void *)((unsigned long)stack_top & ~0xF);
    
    int child_pid = clone(mythread_startup, stack_top, CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD, (void *)mythread);
    if (child_pid == -1) {
        fprintf(stderr, "mythread_create: clone failed: %s\n", strerror(errno));
        free(mythread);
        munmap(child_stack, STACK_SIZE + GUARD_PAGE);
        return -1;
    }
    *thread = mythread;
    return 0;
}

/**
 * Ожидает завершения потока и освобождает его ресурсы.
 * Использует активное ожидание через флаг exited, затем освобождает стек и структуру.
 * @param thread Дескриптор потока
 * @param retval Указатель для возвращаемого значения (может быть NULL)
 * @return 0 при успехе, -1 при ошибке
 */
int mythread_join(mythread_t thread, void **retval) {
    mythread_struct_t *mythread = thread;
    while (!mythread->exited) {
        usleep(1000);
    }
    if (retval) {
        *retval = mythread->retval;
    }
    if (mythread->stack) {
        munmap(mythread->stack, mythread->stack_size);
    }
    free(mythread); 
    return 0;
}

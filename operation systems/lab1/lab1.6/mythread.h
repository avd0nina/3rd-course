#ifndef MYTHREAD_H
#define MYTHREAD_H

#include <stddef.h>

typedef void *(*start_routine_t)(void *);

typedef struct {
    int mythread_id;
    start_routine_t start_routine;
    void *arg;
    void *retval;
    volatile int exited;
    void *stack;
    size_t stack_size;
} mythread_struct_t;

typedef mythread_struct_t *mythread_t;

/**
 * Создаёт новый поток, используя переданную функцию и аргумент.
 * @param thread Указатель для хранения дескриптора потока
 * @param start_routine Функция, выполняемая в потоке
 * @param arg Аргумент для функции потока
 * @return 0 при успехе, -1 при ошибке
 */
int mythread_create(mythread_t *thread, start_routine_t start_routine, void *arg);

/**
 * Ожидает завершения потока и освобождает его ресурсы.
 * @param thread Дескриптор потока
 * @param retval Указатель для возвращаемого значения (может быть NULL)
 * @return 0 при успехе, -1 при ошибке
 */
int mythread_join(mythread_t thread, void **retval);

#endif // MYTHREAD_H

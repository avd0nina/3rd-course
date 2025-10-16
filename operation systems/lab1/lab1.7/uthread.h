#ifndef UTHREAD_H
#define UTHREAD_H

#include <ucontext.h>
#include <pthread.h>

/**
 * Максимальное количество корутин на один воркер.
 */
#define MAX_THREADS_COUNT 8

/**
 * Тип для функции, выполняемой корутиной.
 */
typedef void *(*start_routine_t)(void *);

/**
 * Структура для хранения данных корутины.
 */
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

/**
 * Тип для дескриптора корутины.
 */
typedef uthread_struct_t *uthread_t;

/**
 * Инициализирует библиотеку, создавая пул воркеров.
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_init(void);

/**
 * Создаёт новую корутину.
 * @param thread Указатель для хранения дескриптора корутины.
 * @param start_routine Функция, выполняемая корутиной.
 * @param arg Аргумент для функции корутины.
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_create(uthread_t *thread, start_routine_t start_routine, void *arg);

/**
 * Ожидает завершения корутины и возвращает её результат.
 * @param thread Дескриптор корутины.
 * @param retval Указатель для хранения возвращаемого значения (может быть NULL).
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_join(uthread_t thread, void **retval);

/**
 * Передаёт управление шедулеру корутин.
 */
void uthread_scheduler(void);

/**
 * Очищает ресурсы библиотеки.
 */
void uthread_cleanup(void);

/**
 * Выделяет стек для корутины или шедулера.
 * @param stack Указатель для хранения адреса стека.
 * @param size Размер стека.
 * @return 0 при успехе, -1 при ошибке.
 */
int create_stack(void **stack, size_t size);

/**
 * Состояния корутины.
 */
enum { STATE_READY, STATE_RUNNING, STATE_FINISHED };

#endif // UTHREAD_H

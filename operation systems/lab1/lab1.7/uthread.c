#include "uthread.h"
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/mman.h>
#include <stdlib.h>
#include <stdatomic.h>

#define PAGE 4096
#define STACK_SIZE (PAGE * 8)
#define NUM_WORKERS 4

/**
 * Структура для хранения состояния воркера.
 */
typedef struct worker {
    pthread_t thread;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    ucontext_t sched_ctx;
    void *sched_stack;
    uthread_t ready[MAX_THREADS_COUNT];
    int ready_count;
} worker_t;

static worker_t workers[NUM_WORKERS];
static pthread_key_t worker_key;
static pthread_key_t current_thread_key;
static int initialized = 0;
static int uthread_count = 0;
static void *user_stacks[MAX_THREADS_COUNT];
static uthread_t all_threads[MAX_THREADS_COUNT];
static int next_worker = 0;
static volatile int shutdown_flag = 0;

/**
 * Выделяет память для стека с помощью mmap.
 * @param stack Указатель для хранения адреса стека.
 * @param size Размер стека.
 * @return 0 при успехе, -1 при ошибке.
 */
int create_stack(void **stack, size_t size) {
    *stack = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (*stack == MAP_FAILED) {
        fprintf(stderr, "create_stack: failed mmap: %s\n", strerror(errno));
        return -1;
    }
    memset(*stack, 0x7f, size);
    return 0;
}

/**
 * Запускает функцию корутины и управляет её состоянием.
 * @param arg Указатель на структуру корутины (uthread_t).
 */
static void uthread_startup(void *arg) {
    uthread_t mythread = (uthread_t)arg;
    mythread->retval = mythread->start_routine(mythread->arg);
    mythread->state = STATE_FINISHED;
    pthread_mutex_lock(&mythread->join_mutex);
    pthread_cond_broadcast(&mythread->join_cond);
    pthread_mutex_unlock(&mythread->join_mutex);
}

/**
 * Основной цикл шедулера для воркера.
 * @param wid Идентификатор воркера.
 */
static void scheduler_loop(int wid) {
    worker_t *w = &workers[wid];
    while (!shutdown_flag) {
        pthread_mutex_lock(&w->mutex);
        while (w->ready_count == 0 && !shutdown_flag) {
            pthread_cond_wait(&w->cond, &w->mutex);
        }
        if (shutdown_flag) {
            pthread_mutex_unlock(&w->mutex);
            break;
        }
        uthread_t next = w->ready[--w->ready_count];
        pthread_mutex_unlock(&w->mutex);

        pthread_setspecific(current_thread_key, next);
        next->state = STATE_RUNNING;
        swapcontext(&w->sched_ctx, &next->ucontext);

        if (next->state != STATE_FINISHED) {
            pthread_mutex_lock(&w->mutex);
            if (!shutdown_flag) {
                w->ready[w->ready_count++] = next;
            }
            pthread_mutex_unlock(&w->mutex);
        }
    }
}

/**
 * Функция воркера, инициализирующая шедулер.
 * @param arg Идентификатор воркера (int).
 * @return NULL при завершении.
 */
static void *worker_func(void *arg) {
    int wid = (int)(long)arg;
    worker_t *w = &workers[wid];
    pthread_setspecific(worker_key, w);

    if (create_stack(&w->sched_stack, STACK_SIZE) == -1) {
        fprintf(stderr, "worker_func: failed to create sched stack\n");
        return NULL;
    }

    if (getcontext(&w->sched_ctx) == -1) {
        perror("getcontext");
        return NULL;
    }
    w->sched_ctx.uc_stack.ss_sp = w->sched_stack;
    w->sched_ctx.uc_stack.ss_size = STACK_SIZE;
    w->sched_ctx.uc_link = NULL;
    makecontext(&w->sched_ctx, (void (*)(void))scheduler_loop, 1, wid);

    setcontext(&w->sched_ctx);
    fprintf(stderr, "worker_func: setcontext failed\n");
    return NULL;
}

/**
 * Инициализирует библиотеку, создавая пул воркеров.
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_init(void) {
    if (initialized) {
        fprintf(stderr, "uthread_init: already initialized\n");
        return -1;
    }
    if (pthread_key_create(&worker_key, NULL) != 0 || pthread_key_create(&current_thread_key, NULL) != 0) {
        return -1;
    }
    shutdown_flag = 0;
    next_worker = 0;
    uthread_count = 0;

    for (int i = 0; i < NUM_WORKERS; i++) {
        if (pthread_mutex_init(&workers[i].mutex, NULL) != 0 ||
            pthread_cond_init(&workers[i].cond, NULL) != 0) {
            return -1;
        }
        workers[i].ready_count = 0;
        if (pthread_create(&workers[i].thread, NULL, worker_func, (void *)(long)i) != 0) {
            fprintf(stderr, "uthread_init: failed to create worker %d\n", i);
            return -1;
        }
    }
    initialized = 1;
    return 0;
}

/**
 * Создаёт новую корутину и добавляет её в очередь воркера.
 * @param thread Указатель для хранения дескриптора корутины.
 * @param start_routine Функция, выполняемая корутиной.
 * @param arg Аргумент для функции корутины.
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_create(uthread_t *thread, start_routine_t start_routine, void *arg) {
    if (!initialized) {
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

    int wid = __sync_fetch_and_add(&next_worker, 1) % NUM_WORKERS;
    void *stack = NULL;
    if (create_stack(&stack, STACK_SIZE) == -1) {
        return -1;
    }
    uthread_t new_thread = (uthread_t)((char *)stack + STACK_SIZE - sizeof(uthread_struct_t));
    new_thread->uthread_id = uthread_count;
    new_thread->start_routine = start_routine;
    new_thread->arg = arg;
    new_thread->retval = NULL;
    new_thread->state = STATE_READY;

    if (pthread_mutex_init(&new_thread->join_mutex, NULL) != 0 ||
        pthread_cond_init(&new_thread->join_cond, NULL) != 0) {
        munmap(stack, STACK_SIZE);
        return -1;
    }

    if (getcontext(&new_thread->ucontext) == -1) {
        pthread_mutex_destroy(&new_thread->join_mutex);
        pthread_cond_destroy(&new_thread->join_cond);
        munmap(stack, STACK_SIZE);
        return -1;
    }
    new_thread->ucontext.uc_stack.ss_sp = stack;
    new_thread->ucontext.uc_stack.ss_size = STACK_SIZE - sizeof(uthread_struct_t);
    new_thread->ucontext.uc_link = &workers[wid].sched_ctx;
    makecontext(&new_thread->ucontext, (void (*)(void))uthread_startup, 1, new_thread);

    pthread_mutex_lock(&workers[wid].mutex);
    all_threads[uthread_count] = new_thread;
    user_stacks[uthread_count] = stack;
    workers[wid].ready[workers[wid].ready_count++] = new_thread;
    uthread_count++;
    pthread_cond_signal(&workers[wid].cond);
    pthread_mutex_unlock(&workers[wid].mutex);

    *thread = new_thread;
    return 0;
}

/**
 * Ожидает завершения корутины и возвращает её результат.
 * @param thread Дескриптор корутины.
 * @param retval Указатель для хранения возвращаемого значения (может быть NULL).
 * @return 0 при успехе, -1 при ошибке.
 */
int uthread_join(uthread_t thread, void **retval) {
    if (thread == NULL) {
        fprintf(stderr, "uthread_join: thread is NULL\n");
        return -1;
    }
    pthread_mutex_lock(&thread->join_mutex);
    while (thread->state != STATE_FINISHED) {
        pthread_cond_wait(&thread->join_cond, &thread->join_mutex);
    }
    pthread_mutex_unlock(&thread->join_mutex);
    if (retval) {
        *retval = thread->retval;
    }
    return 0;
}

/**
 * Передаёт управление шедулеру воркера.
 */
void uthread_scheduler(void) {
    uthread_t self = (uthread_t)pthread_getspecific(current_thread_key);
    if (self == NULL) return;
    worker_t *w = (worker_t *)pthread_getspecific(worker_key);
    if (w == NULL) return;
    self->state = STATE_READY;
    swapcontext(&self->ucontext, &w->sched_ctx);
}

/**
 * Очищает ресурсы библиотеки, завершая воркеры и освобождая память.
 */
void uthread_cleanup(void) {
    if (!initialized) return;
    shutdown_flag = 1;
    for (int i = 0; i < NUM_WORKERS; i++) {
        pthread_mutex_lock(&workers[i].mutex);
        pthread_cond_broadcast(&workers[i].cond);
        pthread_mutex_unlock(&workers[i].mutex);
        pthread_join(workers[i].thread, NULL);
        munmap(workers[i].sched_stack, STACK_SIZE);
        pthread_mutex_destroy(&workers[i].mutex);
        pthread_cond_destroy(&workers[i].cond);
    }
    for (int i = 0; i < uthread_count; i++) {
        pthread_mutex_destroy(&all_threads[i]->join_mutex);
        pthread_cond_destroy(&all_threads[i]->join_cond);
        munmap(user_stacks[i], STACK_SIZE);
    }
    pthread_key_delete(worker_key);
    pthread_key_delete(current_thread_key);
    initialized = 0;
}

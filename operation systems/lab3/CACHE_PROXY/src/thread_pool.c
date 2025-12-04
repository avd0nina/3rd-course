#include "thread_pool.h"

#include <errno.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

#include "log.h"

static long id_counter = 0; // Счетчик для генерации уникальных ID задач

/**
 * @brief Функция потока-исполнителя
 * @param arg Указатель на thread_pool_t
 * @return NULL
 * @details Каждый поток-исполнитель выполняет бесконечный цикл:
 *          1. Ждет пока в очереди появится задача
 *          2. Берет задачу из очереди
 *          3. Выполняет задачу (routine)
 *          4. Освобождает ресурсы задачи
 *          5. Повторяет
 *          Цикл прерывается когда устанавливается флаг shutdown.
 */
static void *executor_routine(void *arg);

/**
 * @brief Структура задачи для выполнения в пуле потоков
 * @var id Уникальный идентификатор задачи
 * @var routine Функция для выполнения
 * @var arg Аргумент для функции routine
 */
struct task_t {
    long id;
    void (*routine)(void *arg);
    void *arg;
};
typedef struct task_t task_t;

/**
 * @brief Структура пула потоков
 * @details Реализует пул потоков с циклической очередью задач.
 *          Потоки-исполнители ждут задачи в очереди, выполняют их,
 *          затем возвращаются в ожидание.
 */
struct thread_pool_t {
    // Циклическая очередь задач
    task_t *tasks; // Массив задач
    int capacity; // Размер массива задач
    int size; // Количество задач в очереди
    int front; // Индекс головы очереди
    int rear; // Индекс хвоста очереди
    pthread_mutex_t mutex; // Мьютекс
    pthread_cond_t not_empty_cond; // Условная переменная для сигнализации о том, что очередь не пуста
    pthread_cond_t not_full_cond;  // Условная переменная для сигнализации о том, что очередь не полна
    // Потоки-исполнители
    pthread_t *executors; // Массив потоков
    int num_executors; // Количество потоков
    // Управление завершением
    atomic_int shutdown; // Флаг завершения
};

/**
 * @brief Создает и инициализирует пул потоков
 * @param executor_count Количество потоков-исполнителей в пуле
 * @param task_queue_capacity Максимальное количество задач в очереди
 * @return Указатель на созданный пул потоков или NULL при ошибке
 * @details Алгоритм работы:
 *          1. Выделяет память под структуру пула потоков
 *          2. Создает циклическую очередь задач заданной емкости
 *          3. Инициализирует мьютекс и условные переменные
 *          4. Создает массив для хранения идентификаторов потоков
 *          5. Запускает заданное количество потоков-исполнителей
 *          6. Устанавливает имена потокам
 */
thread_pool_t * thread_pool_create(int executor_count, int task_queue_capacity) {
    errno = 0;
    thread_pool_t *pool = malloc(sizeof(thread_pool_t)); // Выделение памяти под структуру пула потоков
    if (pool == NULL) {
        if (errno == ENOMEM) proxy_log("Thread pool creation error: %s", strerror(errno));
        else proxy_log("Thread pool creation error: failed to reallocate memory");
        return NULL;
    }
    errno = 0;
    pool->tasks = calloc(sizeof(task_t), task_queue_capacity); // Выделяет и обнуляет память для массива задач
    if (pool->tasks == NULL) {
        if (errno == ENOMEM) proxy_log("Thread pool creation error: %s", strerror(errno));
        else proxy_log("Thread pool creation error: failed to reallocate memory");
        free(pool);
        return NULL;
    }
    pool->capacity = task_queue_capacity;
    pool->size = 0;
    pool->front = 0;
    pool->rear = 0;
    pool->shutdown = 0;
    pool->num_executors = executor_count;
    pthread_mutex_init(&pool->mutex, NULL);
    pthread_cond_init(&pool->not_empty_cond, NULL);
    pthread_cond_init(&pool->not_full_cond, NULL);
    errno = 0;
    pool->executors = calloc(sizeof(pthread_t), executor_count); // Выделение памяти для массива идентификаторов потоков
    if (pool->executors == NULL) {
        if (errno == ENOMEM) proxy_log("Thread pool creation error: %s", strerror(errno));
        else proxy_log("Thread pool creation error: failed to reallocate memory");
        pthread_mutex_destroy(&pool->mutex);
        pthread_cond_destroy(&pool->not_empty_cond);
        pthread_cond_destroy(&pool->not_full_cond);
        free(pool);
        return NULL;
    }
    char thread_name[16];
    // Создание потоков-исполнителей
    for (int i = 0; i < executor_count; i++) {
        pthread_create(&pool->executors[i], NULL, executor_routine, pool);
        snprintf(thread_name, 16, "thread-pool-%d", i);
        pthread_setname_np(thread_name);
    }
    return pool;
}

/**
 * @brief Добавляет новую задачу в пул потоков для выполнения
 * @param pool Указатель на структуру пула потоков
 * @param routine Указатель на функцию-задачу, которую нужно выполнить
 * @param arg Аргумент для передачи в функцию routine
 * @details Алгоритм работы:
 *          1. Проверяет, не завершен ли пул (shutdown флаг)
 *          2. Захватывает мьютекс для синхронизации доступа к очереди
 *          3. Ожидает, пока в очереди не появится свободное место
 *          4. Добавляет задачу в циклическую очередь
 *          5. Сигнализирует потокам-исполнителям о новой задаче
 *          6. Освобождает мьютекс
 */
void thread_pool_execute(thread_pool_t *pool, routine_t routine, void *arg) {
    if (pool->shutdown) {
        proxy_log("Thread pool execution error: thread pool was shutdown");
        return;
    }
    pthread_mutex_lock(&pool->mutex); // Захват мьютекса для синхронизации
    while (pool->size == pool->capacity && !pool->shutdown) pthread_cond_wait(&pool->not_full_cond, &pool->mutex); // Проверяет, заполнена ли очередь, и если да - ждет сигнала
    if (pool->shutdown) {
        pthread_mutex_unlock(&pool->mutex);
        return;
    }
    // Помещает новую задачу в конец очереди и обновляет индекс
    pool->tasks[pool->rear].id = id_counter++;
    pool->tasks[pool->rear].routine = routine;
    pool->tasks[pool->rear].arg = arg;
    pool->rear = (pool->rear + 1) % pool->capacity;
    pool->size++;
    // Пробуждает один поток, ожидающий на условной переменной not_empty_cond
    pthread_cond_signal(&pool->not_empty_cond);
    pthread_mutex_unlock(&pool->mutex);
}

/**
 * @brief Полностью останавливает и уничтожает пул потоков
 * @param pool Указатель на структуру пула потоков для остановки
 * @details Алгоритм работы:
 *          1. Устанавливает флаг shutdown в 1
 *          2. Пробуждает все потоки, ожидающие на условных переменных
 *          3. Ожидает завершения всех потоков-исполнителей
 *          4. Освобождает все выделенные ресурсы
 *          5. Уничтожает объекты синхронизации
 *          6. Освобождает память структуры пула
 */
void thread_pool_shutdown(thread_pool_t *pool) {
    pool->shutdown = 1;
    // Пробуждение всех ожидающих потоков
    pthread_cond_broadcast(&pool->not_empty_cond);
    pthread_cond_broadcast(&pool->not_full_cond);
    // Блокирует текущий поток до завершения каждого потока-исполнителя
    for (int i = 0; i < pool->num_executors; i++) pthread_join(pool->executors[i], NULL);
    free(pool->tasks);
    free(pool->executors);
    pthread_mutex_destroy(&pool->mutex);
    pthread_cond_destroy(&pool->not_empty_cond);
    pthread_cond_destroy(&pool->not_full_cond);
    free(pool);
}

/**
 * @brief Функция-исполнитель, выполняющая задачи из очереди пула потоков
 * @param arg Указатель на структуру thread_pool_t
 * @return NULL
 * @details Алгоритм работы потока-исполнителя:
 *          1. Бесконечный цикл ожидания и выполнения задач
 *          2. Захватывает мьютекс для доступа к очереди
 *          3. Ожидает, пока в очереди не появится задача
 *          4. Если пул остановлен - завершает работу потока
 *          5. Извлекает задачу из начала очереди
 *          6. Сигнализирует, что в очереди появилось свободное место
 *          7. Выполняет задачу вне критической секции
 *          8. Возвращается к ожиданию следующей задачи
 */
static void *executor_routine(void *arg) {
    thread_pool_t *pool = (thread_pool_t *) arg;
    // Запускает цикл потока-исполнителя
    while (1) {
        pthread_mutex_lock(&pool->mutex);
        // Ожидание появления задач в очереди
        while (pool->size == 0 && !pool->shutdown) pthread_cond_wait(&pool->not_empty_cond, &pool->mutex);
        if (pool->shutdown) {
            pthread_mutex_unlock(&pool->mutex);
            pthread_exit(NULL);
        }
        // Берет задачу из начала очереди и обновляет состояние
        task_t task = pool->tasks[pool->front]; // Копируем структуру задачи
        pool->front = (pool->front + 1) % pool->capacity; // Увеличиваем front с циклическим переносом
        pool->size--;
        // Пробуждает один поток, ожидающий на not_full_cond
        pthread_cond_signal(&pool->not_full_cond);
        pthread_mutex_unlock(&pool->mutex);
        // Выполнение задачи
        proxy_log("Start executing task %d", task.id);
        task.routine(task.arg);
        proxy_log("Finish executing task %d", task.id);
    }
}

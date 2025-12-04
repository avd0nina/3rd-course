#ifndef CACHE_PROXY_THREAD_POOL_H
#define CACHE_PROXY_THREAD_POOL_H

/**
 * @brief Структура, представляющая пул потоков
 */
struct thread_pool_t;
typedef struct thread_pool_t thread_pool_t;

/**
 * @brief Тип функции, которую могут выполнять потоки пула
 * @param arg Указатель на аргументы функции (может быть NULL)
 */
typedef void (*routine_t)(void *arg);

/**
 * @brief Создает новый пул потоков
 * @details Создает заданное количество потоков-исполнителей и инициализирует
 *          очередь задач с указанной емкостью.
 * @param executor_count Количество потоков-исполнителей в пуле
 * @param task_queue_capacity Максимальное количество задач в очереди
 * @return Указатель на созданный пул потоков или NULL при ошибке
 * @note Если executor_count <= 0, используется значение по умолчанию
 * @note Если task_queue_capacity <= 0, используется неограниченная очередь
 */
thread_pool_t *thread_pool_create(int executor_count, int task_queue_capacity);

/**
 * @brief Добавляет новую задачу в пул потоков для выполнения
 * @details Помещает задачу в очередь. Если есть свободные потоки,
 *          задача будет немедленно взята на выполнение.
 * @param pool Пул потоков для выполнения задачи
 * @param routine Функция для выполнения
 * @param arg Аргумент для передачи в функцию routine
 */
void thread_pool_execute(thread_pool_t *pool, routine_t routine, void *arg);

/**
 * @brief Останавливает пул потоков
 * @details Завершает прием новых задач, дожидается завершения всех
 *          текущих задач в очереди, затем останавливает потоки-исполнители
 *          и освобождает все ресурсы.
 * @param pool Пул потоков для остановки
 * @note Функция блокирует вызывающий поток до полной остановки пула
 * @note Последующие вызовы thread_pool_execute будут игнорироваться
 */
void thread_pool_shutdown(thread_pool_t *pool);

#endif // CACHE_PROXY_THREAD_POOL_H

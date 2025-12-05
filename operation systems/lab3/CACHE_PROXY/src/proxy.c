#include "proxy.h"

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <regex.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "cache.h"
#include "log.h"
#include "thread_pool.h"

#include "../picohttpparser/picohttpparser.h"

#define BUFFER_SIZE             4096
#define CACHE_CAPACITY          100
#define TASK_QUEUE_CAPACITY     100
#define MAX_USERS_COUNT         10
#define ACCEPT_TIMEOUT_MS       1000
#define READ_WRITE_TIMEOUT_MS   60000

#define SUCCESS             0
#define ERROR               (-1)
#define NO_CLIENT           (-2)

/**
 * @brief Единственный экземпляр прокси-сервера (singleton)
 */
static proxy_t *instance = NULL;

/**
 * @brief Обработчик сигналов для завершения работы прокси-сервера
 * @param signal Номер полученного сигнала (не используется)
 * @details Функция-обработчик сигналов, которая инициирует корректное завершение
 *          работы прокси-сервера. Устанавливает флаг running в 0, что приводит
 *          к остановке основного цикла приема соединений.
 * @note Использует __attribute__((unused)) для подавления предупреждений компилятора
 */
static void termination_handler(__attribute__((unused)) int signal);

/**
 * @brief Создает и настраивает серверный сокет для прослушивания входящих соединений
 * @param port Порт, на котором будет работать прокси-сервер
 * @return Дескриптор созданного сокета или ERROR (-1) при ошибке
 * @details Алгоритм создания серверного сокета:
 *          1. Создает TCP сокет (AF_INET, SOCK_STREAM)
 *          2. Устанавливает опцию SO_REUSEADDR для быстрого перезапуска
 *          3. Настраивает структуру адреса (слушает все интерфейсы, заданный порт)
 *          4. Привязывает сокет к адресу (bind)
 *          5. Переводит сокет в режим прослушивания (listen)
 *          6. Логирует успешное создание
 * @note Использует IPv4 (AF_INET), для IPv6 нужно использовать AF_INET6
 * @note Слушает на всех сетевых интерфейсах (INADDR_ANY)
 * @note Максимальная очередь подключений определяется MAX_USERS_COUNT
 */
static int create_server_socket(int port);

/**
 * @brief Принимает входящее клиентское соединение
 * @param server_socket Дескриптор серверного сокета
 * @return Дескриптор клиентского сокета или -1 при ошибке
 */
static int accept_client(int server_socket);

/**
 * @brief Основная функция обработки клиентского HTTP соединения
 * @param arg Указатель на client_handler_context_t (контекст клиента)
 * @details Алгоритм работы:
 *          1. Прием и парсинг HTTP-запроса от клиента
 *          2. Проверка кэша (для GET запросов)
 *          3. Если кэш есть - отдача из кэша
 *          4. Если кэша нет - подключение к целевому серверу
 *          5. Проксирование данных между клиентом и сервером
 *          6. Кэширование ответа (для поддерживаемых запросов)
 *          7. Освобождение ресурсов
 */
static void handle_client(void *arg);

/**
 * @brief Устанавливает TCP соединение с удаленным сервером
 * @param host Имя хоста или IP-адрес целевого сервера
 * @param port Порт целевого сервера
 * @return Дескриптор установленного сокета или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Разрешение имени хоста в IP-адрес
 *          2. Создание TCP сокета
 *          3. Настройка структуры адреса сервера
 *          4. Установка соединения
 *          5. Возврат дескриптора готового сокета
 */
static int connect_to_remote(const char *host, int port);

/**
 * @brief Принимает данные из сокета с таймаутом
 * @param fd Дескриптор сокета для чтения
 * @param buf Буфер для сохранения принятых данных
 * @param buf_len Максимальный размер буфера
 * @return Количество принятых байт, 0 при закрытии соединения, ERROR при ошибке/таймауте
 * @details Алгоритм работы:
 *          1. Использует select() для ожидания доступности данных с таймаутом
 *          2. Если данные доступны, вызывает recv() для их чтения
 *          3. Обрабатывает различные сценарии: данные, таймаут, ошибки, закрытие соединения
 */
static ssize_t receive_with_timeout(int fd, char *buf, size_t buf_len);

/**
 * @brief Отправляет данные в сокет с таймаутом
 * @param fd Дескриптор сокета для записи
 * @param data Данные для отправки
 * @param data_len Длина данных для отправки
 * @return Количество отправленных байт или ERROR при ошибке/таймауте
 * @details Алгоритм работы:
 *          1. Использует select() для ожидания готовности сокета к записи
 *          2. Если сокет готов, вызывает send() для отправки данных
 *          3. Обрабатывает таймауты, ошибки и прерывания
 */
static ssize_t send_with_timeout(int fd, const char *data, size_t data_len);

/**
 * @brief Полностью читает все данные из сокета до закрытия соединения или ошибки
 * @param fd Дескриптор сокета для чтения
 * @param data Указатель на буфер, который будет выделен для хранения всех данных
 * @return Общее количество прочитанных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Инициализирует пустой буфер
 *          2. В цикле читает данные порциями через receive_with_timeout()
 *          3. Перевыделяет буфер для добавления новых данных
 *          4. Копирует полученные данные в буфер
 *          5. Прекращает чтение при закрытии соединения, ошибке или неполном чтении
 * @note Динамически увеличивает буфер по мере чтения данных
 * @note Использует временный буфер фиксированного размера BUFFER_SIZE
 */
static ssize_t receive_full_data(int fd, char **data);

/**
 * @brief Гарантированно отправляет все данные через сокет с поддержкой таймаутов
 * @param fd Дескриптор сокета для отправки данных
 * @param data Указатель на данные для отправки
 * @param data_len Общее количество байт для отправки
 * @return Общее количество успешно отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. В цикле отправляет данные порциями через send_with_timeout()
 *          2. После каждой успешной отправки сдвигает указатель на оставшиеся данные
 *          3. Продолжает отправку, пока не будут отправлены все data_len байт
 *          4. Возвращает общее количество отправленных байт (должно равняться data_len)
 */
static ssize_t send_full_data(int fd, const char *data, size_t data_len);

/**
 * @brief Принимает данные из одного сокета и одновременно отправляет в другой
 * @param ifd Входной файловый дескриптор (input fd) - откуда читать данные
 * @param ofd Выходной файловый дескриптор (output fd) - куда отправлять данные
 * @param data Указатель на буфер для сохранения принятых данных
 * @return Общее количество прочитанных и пересланных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Читает порцию данных из ifd с помощью receive_with_timeout()
 *          2. Немедленно отправляет эту порцию в ofd с помощью send_with_timeout()
 *          3. Сохраняет данные в буфер *data (если не NULL) для последующей обработки
 *          4. Повторяет до закрытия соединения или ошибки
 * @note Одновременно выполняет чтение, отправку и сохранение данных
 */
static ssize_t receive_and_send_data(int ifd, int ofd, char **data);

/**
 * @brief Принимает, отправляет и собирает структурированное сообщение
 * @param ifd Входной файловый дескриптор (input fd) - откуда читать данные
 * @param ofd Выходной файловый дескриптор (output fd) - куда отправлять данные
 * @param message Указатель на указатель структуры message_t для сборки сообщения
 * @return Общее количество отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Читает порцию данных из ifd через receive_with_timeout()
 *          2. Немедленно отправляет порцию в ofd через send_with_timeout()
 *          3. Добавляет порцию в структурированное сообщение через message_add_part()
 *          4. Повторяет до закрытия соединения, ошибки или неполного чтения
 */
static ssize_t receive_and_send_message(int ifd, int ofd, message_t **message);

/**
 * @brief Отправляет кэшированные данные клиенту с поддержкой потоковой загрузки
 * @param entry Указатель на запись в кэше, содержащую данные для отправки
 * @param client_socket Дескриптор клиентского сокета для отправки данных
 * @return Общее количество отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Блокирует мьютекс записи в кэше для безопасного доступа
 *          2. Проходит по цепочке message_t в entry->response
 *          3. Для каждой части сообщения:
 *             а) Отправляет данные клиенту через send_full_data()
 *             б) Обновляет счетчик отправленных байт
 *          4. Если данные еще не полностью загружены в кэш, ожидает на condition variable
 *          5. Просыпается при добавлении новых данных или завершении загрузки
 *          6. Продолжает отправку, пока все данные не будут отправлены
 */
static ssize_t stream_cache_to_client(cache_entry_t *entry, int client_socket);

/**
 * @brief Извлекает хост и порт из строки URL или адреса сервера
 * @param host_port Входная строка (URL или "host:port")
 * @param host Буфер для сохранения имени хоста
 * @param port Указатель на переменную для сохранения номера порта
 * @return 0 при успехе, ERROR (-1) при ошибке парсинга
 * @details Алгоритм работы:
 *          1. Компилирует регулярное выражение для парсинга URL
 *          2. Выполняет сопоставление регулярного выражения со входной строкой
 *          3. Извлекает хост из соответствующей группы
 *          4. Извлекает порт, если указан, иначе использует порт по умолчанию
 *          5. Определяет порт по умолчанию на основе схемы (http/https)
 *          6. Освобождает ресурсы регулярного выражения
 */
static int get_host_port(const char *host_port, char *host, int *port);

/**
 * @brief Парсит HTTP-запрос и извлекает метод и заголовок Host
 * @param request Строка с HTTP-запросом
 * @param request_len Длина строки запроса
 * @param method Указатель для сохранения указателя на метод в request
 * @param method_len Указатель для сохранения длины метода
 * @param host Указатель для сохранения указателя на значение Host в request
 * @param host_len Указатель для сохранения длины значения Host
 * @return SUCCESS (0) при успехе, ERROR (-1) при ошибке
 * @details Алгоритм работы:
 *          1. Использует библиотеку PicoHTTPParser для парсинга HTTP-запроса
 *          2. Извлекает метод HTTP (GET, POST, CONNECT и т.д.)
 *          3. Ищет заголовок Host в списке заголовков
 *          4. Сохраняет указатели на метод и Host в исходном буфере
 */
static int parse_request(const char *request, size_t request_len, const char **method, size_t *method_len, const char **host, size_t *host_len);

/**
 * @brief Парсит HTTP-ответ и извлекает статус, длину контента и позицию заголовка Content-Length
 * @param response Строка с HTTP-ответом
 * @param response_len Длина строки ответа
 * @param status Указатель для сохранения HTTP статус-кода (200, 404, 500 и т.д.)
 * @param content_len Указатель для сохранения фактической длины тела ответа
 * @param content_length_header Указатель для сохранения значения заголовка Content-Length
 * @return SUCCESS (0) при успехе, ERROR (-1) при ошибке
 * @details Алгоритм работы:
 *          1. Использует PicoHTTPParser для парсинга HTTP-ответа
 *          2. Извлекает HTTP статус-код
 *          3. Ищет заголовок Content-Length и парсит его значение
 *          4. Вычисляет фактическую длину тела ответа
 *          5. Проверяет корректность формата ответа
 */
static int parse_response(const char *response, size_t response_len, int *status, size_t *content_len, size_t *content_length_header);

/**
 * @brief Проверяет, является ли HTTP-запрос кэшируемым
 * @param method Указатель на строку с HTTP-методом
 * @param method_len Длина строки метода
 * @return 1 (true) если метод кэшируемый, 0 (false) если нет
 * @details В текущей реализации кэшируются только GET-запросы.
 */
static int check_request(const char *method, size_t method_len);

/**
 * @brief Проверяет, является ли HTTP-ответ кэшируемым на основе статус-кода
 * @param status HTTP статус-код ответа (200, 404, 500 и т.д.)
 * @return 1 (true) если ответ можно кэшировать, 0 (false) если нет
 * @details В текущей реализации кэшируются все ответы со статусом < 400.
 * @note Кэшируются успешные ответы (2xx) и перенаправления (3xx)
 * @note Не кэшируются клиентские (4xx) и серверные (5xx) ошибки
 */
static int check_response(int status);

/**
 * @brief Находит запись в кэше и ожидает её готовности если необходимо
 * @param cache Указатель на структуру кэша
 * @param request Строка HTTP-запроса для поиска
 * @param request_len Длина строки запроса
 * @return Указатель на найденную запись кэша или NULL если не найдено/удалено
 * @details Алгоритм работы:
 *          1. Ищет запись в кэше по запросу с помощью cache_get()
 *          2. Если запись найдена, но ответ еще не готов (entry->response == NULL):
 *             а) Блокирует мьютекс записи
 *             б) Ожидает на condition variable, пока данные не появятся или запись не удалят
 *             в) Проверяет, не была ли запись удалена во время ожидания
 *             г) Разблокирует мьютекс
 *          3. Возвращает найденную запись или NULL
 * @note Реализует паттерн "ожидание готовности данных" для конкурентного доступа
 * @note Позволяет нескольким клиентам ждать одну и ту же загружаемую запись
 * @note Обрабатывает случай удаления записи во время ожидания
 * @note Гарантирует потокобезопасный доступ к записи кэша
 */
static cache_entry_t *find_cache_entry(cache_t *cache, const char *request, size_t request_len);

/**
 * @brief Структура прокси-сервера
 * @details Содержит все состояние прокси-сервера:
 *          - Кэш HTTP-ответов
 *          - Мьютекс для синхронизации доступа к кэшу
 *          - Пул потоков для обработки клиентов
 *          - Атомарный флаг работы сервера
 */
struct proxy_t {
    cache_t *cache;
    pthread_mutex_t cache_mutex;
    thread_pool_t *handlers;
    atomic_int running;
};

/**
 * @brief Контекст обработчика клиента
 * @details Передается в handle_client при создании задачи в пуле потоков.
 * Содержит всю необходимую информацию для обработки клиентского соединения.
 */
struct client_handler_context_t {
    proxy_t *proxy;
    int client_socket;
};
typedef struct client_handler_context_t client_handler_context_t;

/**
 * @brief Создает и инициализирует экземпляр прокси-сервера
 * @param handler_count Количество потоков-обработчиков в пуле
 * @param cache_expired_time_ms Время жизни записей в кэше
 * @return Указатель на созданный прокси-сервер или NULL при ошибке
 * @details Алгоритм работы:
 *          1. Выделяет память под структуру proxy_t
 *          2. Инициализирует кэш HTTP-ответов с заданным временем жизни
 *          3. Создает пул потоков для обработки клиентских соединений
 *          4. Инициализирует мьютекс для синхронизации доступа к кэшу
 *          5. Устанавливает флаг running в 1 (сервер работает)
 */
proxy_t *proxy_create(int handler_count, time_t cache_expired_time_ms) {
    errno = 0;
    proxy_t *proxy = malloc(sizeof(proxy_t)); // Выделение памяти под основную структуру прокси
    if (proxy == NULL) {
        if (errno == ENOMEM) proxy_log("Proxy creation error: %s", strerror(errno));
        else proxy_log("Proxy creation error: failed to reallocate memory");
        return NULL;
    }
    proxy->cache = cache_create(CACHE_CAPACITY, cache_expired_time_ms); // Создает структуру кэша с заданными параметрам
    if (proxy->cache == NULL) {
        free(proxy);
        return NULL;
    }
    proxy->handlers = thread_pool_create(handler_count, TASK_QUEUE_CAPACITY); // Создает пул потоков с заданным количеством обработчиков
    if (proxy->handlers == NULL) {
        cache_destroy(proxy->cache);
        free(proxy);
        return NULL;
    }
    pthread_mutex_init(&proxy->cache_mutex, NULL); // Инициализирует мьютекс
    proxy->running = 1; // Устанавливает флаг работы
    return proxy;
}

/**
 * @brief Запускает прокси-сервер и начинает обработку входящих соединений
 * @param proxy Указатель на инициализированную структуру прокси
 * @param port Порт, на котором будет работать прокси-сервер
 * @details Алгоритм работы:
 *          1. Проверяет корректность переданного указателя proxy
 *          2. Сохраняет proxy в глобальной переменной instance (singleton)
 *          3. Регистрирует обработчики сигналов для graceful shutdown
 *          4. Создает серверный сокет для прослушивания порта
 *          5. В основном цикле принимает клиентские соединения
 *          6. Для каждого соединения создает контекст и отправляет в пул потоков
 *          7. При получении сигнала остановки корректно завершает работу
 */
void proxy_start(proxy_t *proxy, int port) {
    if (proxy == NULL) {
        proxy_log("Proxy starting error: proxy is NULL");
        return;
    }
    instance = proxy; // Сохраняет экземпляр прокси в глобальную переменную
    signal(SIGINT, termination_handler); // Регистрирует обработчик сигналов
    signal(SIGTERM, termination_handler);
    int server_socket = create_server_socket(port); // Создает серверный сокет
    if (server_socket == ERROR) goto delete_proxy_instance;
    while (proxy->running) { // В основном цикле принимает клиентские соединения
        int client_socket = accept_client(server_socket);
        if (client_socket == NO_CLIENT) continue;
        if (client_socket == ERROR) goto close_server_socket;
        errno = 0;
        client_handler_context_t *ctx = malloc(sizeof(client_handler_context_t)); // Выделение памяти под контекст
        if (ctx == NULL) {
            if (errno == ENOMEM) proxy_log("Client handler context creation error: %s", strerror(errno));
            else proxy_log("Client handler context creation error: failed to reallocate memory");
            close(client_socket);
            goto close_server_socket;
        }
        ctx->client_socket = client_socket; // Сохраняет дескриптор клиентского соединения
        ctx->proxy = proxy; // Сохраняет указатель на экземпляр прокси
        thread_pool_execute(proxy->handlers, handle_client, ctx); // Отправляет контекст в пул потоков
    }
    close_server_socket:
    close(server_socket);
    delete_proxy_instance:
    instance = NULL;
}

/**
 * @brief Уничтожает экземпляр прокси-сервера и освобождает все ресурсы
 * @param proxy Указатель на структуру proxy_t для уничтожения
 * @details Алгоритм работы:
 *          1. Проверяет валидность указателя proxy
 *          2. Останавливает пул потоков-обработчиков
 *          3. Уничтожает кэш HTTP-ответов
 *          4. Уничтожает мьютекс синхронизации кэша
 *          5. Освобождает память структуры proxy
 *          6. Сбрасывает глобальный указатель instance в NULL
 */
void proxy_destroy(proxy_t *proxy) {
    if (proxy == NULL) {
        proxy_log("Proxy destroying error: proxy is NULL");
        return;
    }
    proxy_log("Destroy handlers");
    thread_pool_shutdown(proxy->handlers); // Остановка пула потоков-обработчиков
    proxy_log("Destroy cache");
    cache_destroy(proxy->cache); // Освобождает все ресурсы, связанные с кэшем
    pthread_mutex_destroy(&proxy->cache_mutex); // Уничтожение мьютекса синхронизации кэша
    proxy_log("Destroy proxy");
    free(proxy); // Освобождает память, выделенную под структуру proxy_t
    instance = NULL;
}

/**
 * @brief Обработчик сигналов для завершения работы прокси-сервера
 * @param signal Номер полученного сигнала (не используется)
 * @details Функция-обработчик сигналов, которая инициирует корректное завершение
 *          работы прокси-сервера. Устанавливает флаг running в 0, что приводит
 *          к остановке основного цикла приема соединений.
 * @note Использует __attribute__((unused)) для подавления предупреждений компилятора
 */
static void termination_handler(__attribute__((unused)) int signal) {
    if (instance != NULL && instance->running) {
        instance->running = 0;
        proxy_log("Wait for the job to complete");
    }
}

/**
 * @brief Создает и настраивает серверный сокет для прослушивания входящих соединений
 * @param port Порт, на котором будет работать прокси-сервер
 * @return Дескриптор созданного сокета или ERROR (-1) при ошибке
 * @details Алгоритм создания серверного сокета:
 *          1. Создает TCP сокет (AF_INET, SOCK_STREAM)
 *          2. Устанавливает опцию SO_REUSEADDR для быстрого перезапуска
 *          3. Настраивает структуру адреса (слушает все интерфейсы, заданный порт)
 *          4. Привязывает сокет к адресу (bind)
 *          5. Переводит сокет в режим прослушивания (listen)
 *          6. Логирует успешное создание
 * @note Использует IPv4 (AF_INET), для IPv6 нужно использовать AF_INET6
 * @note Слушает на всех сетевых интерфейсах (INADDR_ANY)
 * @note Максимальная очередь подключений определяется MAX_USERS_COUNT
 */
static int create_server_socket(int port) {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0); // Создание TCP сокета
    if (server_socket == ERROR) {
        proxy_log("Creating server socket error: %s", strerror(errno));
        return ERROR;
    }
    int true = 1;
    setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &true, sizeof(int)); // Разрешает повторное использование локального адреса
    struct sockaddr_in server_addr; // Инициализирует структуру sockaddr_in для bind()
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET; // IPv4
    server_addr.sin_addr.s_addr = INADDR_ANY; // все интерфейсы
    server_addr.sin_port = htons(port); // порт в сетевом порядке
    int err = bind(server_socket, (struct sockaddr *) &server_addr, sizeof(server_addr)); // Связывает сокет с конкретным сетевым адресом и портом
    if (err == ERROR) {
        proxy_log("Bind socket error: %s", strerror(errno));
        close(server_socket);
        return ERROR;
    }
    err = listen(server_socket, MAX_USERS_COUNT); // Перевод сокета в режим прослушивания (listen)
    if (err == ERROR) {
        proxy_log("Listen socket error: %s", strerror(errno));
        close(server_socket);
        return ERROR;
    }
    proxy_log("Proxy listen on port %d", port);
    return server_socket;
}

/**
 * @brief Принимает входящее клиентское соединение с таймаутом
 * @param server_socket Дескриптор серверного сокета в режиме прослушивания
 * @return Дескриптор клиентского сокета, NO_CLIENT если нет соединений, ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Ожидает готовности серверного сокета к accept() с помощью select() и таймаутом
 *          2. При наличии соединения принимает его через accept()
 *          3. Устанавливает клиентский сокет в неблокирующий режим
 *          4. Логирует информацию о подключившемся клиенте
 *          5. Возвращает дескриптор клиентского сокета
 */
static int accept_client(int server_socket) {
    fd_set read_fds; //  Подготавливает набор файловых дескрипторов для мониторинга
    FD_ZERO(&read_fds);
    FD_SET(server_socket, &read_fds);
    struct timeval timeout; // Настройка таймаута для select()
    timeout.tv_sec = ACCEPT_TIMEOUT_MS / 1000;
    timeout.tv_usec = (ACCEPT_TIMEOUT_MS % 1000) * 1000;
    int ready = select(server_socket + 1, &read_fds, NULL, NULL, &timeout); // Ожидает, пока серверный сокет не будет готов к accept(). select() позволяет одному потоку следить за множеством файловых дескрипторов и ждать, пока хотя бы один из них не будет готов для операций ввода/вывода
    if (ready == ERROR) {
        if (errno != EINTR) proxy_log("Accept client error: %s", strerror(errno));
        return ERROR;
    }
    else if (ready == 0) return NO_CLIENT; // Если select() вернул 0 (таймаут истек), возвращает NO_CLIENT
    struct sockaddr_in client_addr; // для хранения адреса клиента
    socklen_t client_addr_size = sizeof(client_addr); // размер структуры
    int client_socket = accept(server_socket, (struct sockaddr *) &client_addr, &client_addr_size); // Принимает ожидающее соединение из очереди серверного сокета
    if (client_socket == ERROR) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) return NO_CLIENT;
        else {
            proxy_log("Accept client error: %s", strerror(errno));
            return ERROR;
        }
    }
    int flags = fcntl(client_socket, F_GETFL, 0); //  Получить текущие настройки сокета
    fcntl(client_socket, F_SETFL, flags | O_NONBLOCK); // Добавить флаг O_NONBLOCK (бит отвечающий за неблокирующий режим)
    proxy_log("Accept client %s:%d", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
    return client_socket;
}

/**
 * @brief Основная функция обработки клиентского HTTP соединения
 * @param arg Указатель на client_handler_context_t (контекст клиента)
 * @details Алгоритм работы:
 *          1. Прием и парсинг HTTP-запроса от клиента
 *          2. Проверка кэша (для GET запросов)
 *          3. Если кэш есть - отдача из кэша
 *          4. Если кэша нет - подключение к целевому серверу
 *          5. Проксирование данных между клиентом и сервером
 *          6. Кэширование ответа (для поддерживаемых запросов)
 *          7. Освобождение ресурсов
 */
static void handle_client(void *arg) {
    if (arg == NULL) {
        proxy_log("Proxy error: client handler context is NULL");
        return;
    }
    client_handler_context_t *ctx = (client_handler_context_t *) arg;
    char *request = NULL;
    ssize_t request_len = receive_full_data(ctx->client_socket, &request); // Полностью читает HTTP-запрос от клиента
    if (request_len == ERROR) goto destroy_ctx;
    char *method, *host_port;
    size_t method_len, host_len;
    // Извлекает из запроса метод и хост
    if (parse_request(request, request_len, (const char **) &method, &method_len, (const char **) &host_port, &host_len) == ERROR) goto destroy_ctx;
    cache_entry_t *entry = NULL;
    if (check_request(method, method_len)) { // определяет, можно ли кэшировать запрос
        pthread_mutex_lock(&ctx->proxy->cache_mutex);
        entry = find_cache_entry(ctx->proxy->cache, request, request_len); // Ищем запись
        if (entry != NULL) { // если нашли
            pthread_mutex_unlock(&ctx->proxy->cache_mutex);
            proxy_log("Cache hit, start streaming from cache");
            stream_cache_to_client(entry, ctx->client_socket); // Отдаем из кэша
            goto destroy_ctx;
        }
        entry = cache_entry_create(request, request_len, NULL); // // CACHE MISS - создаем новую запись
        if (entry == NULL) {
            pthread_mutex_unlock(&ctx->proxy->cache_mutex);
            goto destroy_ctx;
        }
        if (cache_add(ctx->proxy->cache, entry) == ERROR) {
            pthread_mutex_unlock(&ctx->proxy->cache_mutex);
            cache_entry_destroy(entry);
            goto destroy_ctx;
        }
        pthread_mutex_unlock(&ctx->proxy->cache_mutex);
    }
    proxy_log("Cache miss"); // Если не нашли
    char host_port1[BUFFER_SIZE];
    strncpy(host_port1, host_port, host_len); // Извлекает хост
    char host[BUFFER_SIZE];
    int port;
    get_host_port(host_port1, host, &port); // Извлекает порт
    int remote_socket = connect_to_remote(host, port); // Устанавливает TCP соединение с целевым сервером
    if (remote_socket == ERROR) goto destroy_entry;
    if (send_full_data(remote_socket, request, request_len) == ERROR) goto destroy_entry; // Пересылка запроса серверу
    char *response_data = NULL;
    ssize_t response_data_len = receive_and_send_data(remote_socket, ctx->client_socket, &response_data); // Принимает ответ от сервера и сразу отправляет клиенту
    if (response_data_len == ERROR) {
        if (response_data != NULL) free(response_data);
        goto destroy_entry;
    }
    // Парсинг HTTP-ответа
    int status;
    size_t content_length_header;
    size_t content_len;
    if (parse_response(response_data, response_data_len, &status, &content_len, &content_length_header) == ERROR) {
        free(response_data);
        goto destroy_entry;
    }
    message_t *response = NULL;
    message_add_part(&response, response_data, response_data_len); // Сохранение первой части ответа для кэша
    // Уведомление ждущих потоков о частичном ответе
    if (check_request(method, method_len)) {
        entry->response = response;
        pthread_mutex_lock(&entry->mutex);
        pthread_cond_broadcast(&entry->ready_cond);
        pthread_mutex_unlock(&entry->mutex);
    }
    // Читает и пересылает оставшуюся часть ответа
    while (content_len < content_length_header) {
        response_data_len = receive_and_send_message(remote_socket, ctx->client_socket, &response);
        if (response_data_len == ERROR) {
            message_destroy(&response);
            goto destroy_entry;
        }
        // Так реализуется streaming кэша: клиенты получают данные по мере загрузки
        // Уведомление ждущих потоков о частичном ответе
        content_len += response_data_len;
        if (check_request(method, method_len)) {
            pthread_mutex_lock(&entry->mutex);
            pthread_cond_broadcast(&entry->ready_cond);
            pthread_mutex_unlock(&entry->mutex);
        }
    }
    // Проверка, можно ли кэшировать ответ
    if (!check_response(status)) goto destroy_entry;
    if (check_request(method, method_len)) {
        entry->finished = 1;
        entry->response = response;
        pthread_mutex_lock(&entry->mutex);
        pthread_cond_broadcast(&entry->ready_cond);
        pthread_mutex_unlock(&entry->mutex);
        proxy_log("Set response to entry");
    }
    goto destroy_ctx;
    destroy_entry:
    if (check_request(method, method_len)) {
        size_t deleted_request_len = entry->request_len;
        char *deleted_request = entry->request;
        pthread_mutex_lock(&entry->mutex);
        entry->deleted = 1;
        pthread_mutex_unlock(&entry->mutex);
        pthread_cond_broadcast(&entry->ready_cond);
        cache_delete(ctx->proxy->cache, deleted_request, deleted_request_len);
    }
    destroy_ctx:
    close(ctx->client_socket);
    free(ctx);
}

/**
 * @brief Устанавливает TCP соединение с удаленным сервером
 * @param host Имя хоста или IP-адрес целевого сервера
 * @param port Порт целевого сервера
 * @return Дескриптор установленного сокета или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Разрешение имени хоста в IP-адрес
 *          2. Создание TCP сокета
 *          3. Настройка структуры адреса сервера
 *          4. Установка соединения
 *          5. Возврат дескриптора готового сокета
 */
static int connect_to_remote(const char *host, int port) {
    struct hostent *h = gethostbyname(host); // Преобразуетт имя хоста в IP-адрес
    if (h == NULL) {
        proxy_log("Connect to remote error: %s", hstrerror(h_errno));
        return ERROR;
    }
    // Заполняет структуру sockaddr_in для connect()
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_port = htons(port);
    addr.sin_family = AF_INET;
    memcpy(&addr.sin_addr, h->h_addr, h->h_length);
    // Создает TCP сокет
    int remote_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (remote_socket == ERROR) {
        proxy_log("Connect to remote error: %s", strerror(errno));
        return ERROR;
    }
    if (connect(remote_socket, (struct sockaddr *) &addr, sizeof(struct sockaddr_in)) == ERROR) { // Устанавливает соединение
        proxy_log("Connect to remote error: %s", strerror(errno));
        close(remote_socket);
        return ERROR;
    }
    return remote_socket;
}

/**
 * @brief Принимает данные из сокета с таймаутом
 * @param fd Дескриптор сокета для чтения
 * @param buf Буфер для сохранения принятых данных
 * @param buf_len Максимальный размер буфера
 * @return Количество принятых байт, 0 при закрытии соединения, ERROR при ошибке/таймауте
 * @details Алгоритм работы:
 *          1. Использует select() для ожидания доступности данных с таймаутом
 *          2. Если данные доступны, вызывает recv() для их чтения
 *          3. Обрабатывает различные сценарии: данные, таймаут, ошибки, закрытие соединения
 */
static ssize_t receive_with_timeout(int fd, char *buf, size_t buf_len) {
    // Подготавливает набор дескрипторов для мониторинга
    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(fd, &read_fds);
    // Настройка таймаута для select()
    struct timeval timeout;
    timeout.tv_sec  = READ_WRITE_TIMEOUT_MS / 1000;
    timeout.tv_usec = (READ_WRITE_TIMEOUT_MS % 1000) * 1000;
    int ready = select(fd + 1, &read_fds, NULL, NULL, &timeout); // Ждет, пока в сокете не появятся данные для чтения
    if (ready == -1) {
        if (errno != EINTR) {
            proxy_log("Data receiving error: %s", strerror(errno));
        }
        return ERROR;
    }
    if (ready == 0) {
        proxy_log("Data receiving error: timeout");
        return ERROR;
    }
    ssize_t received_bytes = recv(fd, buf, buf_len, 0); // Чтение данных из сокета
    if (received_bytes < 0) {
        proxy_log("Data receiving error: %s", strerror(errno));
        return ERROR;
    }
    return received_bytes;
}

/**
 * @brief Отправляет данные в сокет с таймаутом
 * @param fd Дескриптор сокета для записи
 * @param data Данные для отправки
 * @param data_len Длина данных для отправки
 * @return Количество отправленных байт или ERROR при ошибке/таймауте
 * @details Алгоритм работы:
 *          1. Использует select() для ожидания готовности сокета к записи
 *          2. Если сокет готов, вызывает send() для отправки данных
 *          3. Обрабатывает таймауты, ошибки и прерывания
 */
static ssize_t send_with_timeout(int fd, const char *data, size_t data_len) {
    // Подготавливает набор дескрипторов для мониторинга возможности записи
    fd_set write_fds;
    FD_ZERO(&write_fds);
    FD_SET(fd, &write_fds);
    // Настройка таймаута
    struct timeval timeout;
    timeout.tv_sec = READ_WRITE_TIMEOUT_MS / 1000;
    timeout.tv_usec = (READ_WRITE_TIMEOUT_MS % 1000) * 1000;
    int ready = select(fd + 1, NULL, &write_fds, NULL, &timeout); // Ждет, пока сокет не будет готов для операции отправки
    if (ready == -1) {
        if (errno != EINTR) proxy_log("Data sending error: %s", strerror(errno));
        return ERROR;
    } else if (ready == 0) {
        proxy_log("Data sending error: timeout");
        return ERROR;
    }
    ssize_t sent_bytes = send(fd, data, data_len, 0); // Пытается отправить все данные за один вызов
    if (sent_bytes == ERROR) {
        proxy_log("Data sending error: %s", strerror(errno));
        return ERROR;
    }
    proxy_log("Sent: %s", data);
    return sent_bytes;
}

/**
 * @brief Полностью читает все данные из сокета до закрытия соединения или ошибки
 * @param fd Дескриптор сокета для чтения
 * @param data Указатель на буфер, который будет выделен для хранения всех данных
 * @return Общее количество прочитанных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Инициализирует пустой буфер
 *          2. В цикле читает данные порциями через receive_with_timeout()
 *          3. Перевыделяет буфер для добавления новых данных
 *          4. Копирует полученные данные в буфер
 *          5. Прекращает чтение при закрытии соединения, ошибке или неполном чтении
 * @note Динамически увеличивает буфер по мере чтения данных
 * @note Использует временный буфер фиксированного размера BUFFER_SIZE
 */
static ssize_t receive_full_data(int fd, char **data) {
    *data = NULL;
    ssize_t all_received_bytes = 0; // Инициализация счетчика прочитанных байт
    char buf[BUFFER_SIZE + 1]; // Объявление временного буфера
    while (1) {
        memset(buf, 0, BUFFER_SIZE);
        ssize_t received_bytes = receive_with_timeout(fd, buf, BUFFER_SIZE); // Читает до BUFFER_SIZE байт из сокета с таймаутом
        if (received_bytes == ERROR) return ERROR;
        if (received_bytes == 0) break;
        all_received_bytes += received_bytes;
        char *temp = realloc(*data, all_received_bytes + 1); // Перевыделение основного буфера
        if (temp == NULL) {
            if (errno == ENOMEM) proxy_log("Data receiving error: %s", strerror(errno));
            else proxy_log("Data receiving error: failed to reallocate memory");
            free(*data);
            *data = NULL;
            return ERROR;
        }
        *data = temp;
        strncpy(*data + all_received_bytes - received_bytes, buf, received_bytes); // Копирование данных из временного буфера в основной
        if (received_bytes < BUFFER_SIZE) break;
    }
    return all_received_bytes;
}

/**
 * @brief Гарантированно отправляет все данные через сокет с поддержкой таймаутов
 * @param fd Дескриптор сокета для отправки данных
 * @param data Указатель на данные для отправки
 * @param data_len Общее количество байт для отправки
 * @return Общее количество успешно отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. В цикле отправляет данные порциями через send_with_timeout()
 *          2. После каждой успешной отправки сдвигает указатель на оставшиеся данные
 *          3. Продолжает отправку, пока не будут отправлены все data_len байт
 *          4. Возвращает общее количество отправленных байт (должно равняться data_len)
 */
static ssize_t send_full_data(int fd, const char *data, size_t data_len) {
    ssize_t all_sent_bytes = 0; // Инициализация счетчика отправленных байт
    // Запускает цикл, который будет отправлять данные до тех пор, пока не будут отправлены все data_len байт
    while (1) {
        ssize_t sent_bytes = send_with_timeout(fd, data + all_sent_bytes, data_len - all_sent_bytes);
        if (sent_bytes == ERROR) return ERROR;
        all_sent_bytes += sent_bytes;
        if ((size_t) all_sent_bytes == data_len) break;
    }
    return all_sent_bytes;
}

/**
 * @brief Принимает данные из одного сокета и одновременно отправляет в другой
 * @param ifd Входной файловый дескриптор (input fd) - откуда читать данные
 * @param ofd Выходной файловый дескриптор (output fd) - куда отправлять данные
 * @param data Указатель на буфер для сохранения принятых данных
 * @return Общее количество прочитанных и пересланных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Читает порцию данных из ifd с помощью receive_with_timeout()
 *          2. Немедленно отправляет эту порцию в ofd с помощью send_with_timeout()
 *          3. Сохраняет данные в буфер *data (если не NULL) для последующей обработки
 *          4. Повторяет до закрытия соединения или ошибки
 * @note Одновременно выполняет чтение, отправку и сохранение данных
 */
static ssize_t receive_and_send_data(int ifd, int ofd, char **data) {
    char buf[BUFFER_SIZE + 1]; // Временный буфер для чтения порций данных
    ssize_t all_received_bytes = 0; // Счетчик всех принятых байт
    // Запускает цикл чтения-отправки данных до ошибки, либо закрытия входного соединения, либо частичного чтения
    while (1) {
        memset(buf, 0, BUFFER_SIZE);
        ssize_t received_bytes = receive_with_timeout(ifd, buf, BUFFER_SIZE); // Чтение порции данных из входного сокета
        if (received_bytes == ERROR) return ERROR;
        if (received_bytes == 0) break;
        ssize_t sent_bytes = send_with_timeout(ofd, buf, received_bytes); // Отправка прочитанных данных в выходной сокет
        if (sent_bytes == ERROR) return ERROR;
        all_received_bytes += received_bytes;
        char *temp = realloc(*data, all_received_bytes); // Расширяет буфер *data для сохранения прочитанных данных
        if (temp == NULL) {
            if (errno == ENOMEM) proxy_log("Data receiving error: %s", strerror(errno));
            else proxy_log("Data receiving error: failed to reallocate memory");
            free(*data);
            *data = NULL;
            return ERROR;
        }
        *data = temp;
        strncpy(*data + all_received_bytes - received_bytes, buf, received_bytes); // Копирование данных из временного буфера в основной
        if (received_bytes < BUFFER_SIZE) break;
    }
    return all_received_bytes;
}

/**
 * @brief Принимает, отправляет и собирает структурированное сообщение
 * @param ifd Входной файловый дескриптор (input fd) - откуда читать данные
 * @param ofd Выходной файловый дескриптор (output fd) - куда отправлять данные
 * @param message Указатель на указатель структуры message_t для сборки сообщения
 * @return Общее количество отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Читает порцию данных из ifd через receive_with_timeout()
 *          2. Немедленно отправляет порцию в ofd через send_with_timeout()
 *          3. Добавляет порцию в структурированное сообщение через message_add_part()
 *          4. Повторяет до закрытия соединения, ошибки или неполного чтения
 */
static ssize_t receive_and_send_message(int ifd, int ofd, message_t **message) {
    char buf[BUFFER_SIZE + 1];
    ssize_t all_sent_bytes = 0;
    while (1) {
        memset(buf, 0, BUFFER_SIZE);
        ssize_t received_bytes = receive_with_timeout(ifd, buf, BUFFER_SIZE);
        if (received_bytes == ERROR) return ERROR;
        if (received_bytes == 0) break;
        ssize_t sent_bytes = send_with_timeout(ofd, buf, received_bytes);
        if (sent_bytes == ERROR) return ERROR;
        if (message_add_part(message, buf, received_bytes) == ERROR) return ERROR;
        all_sent_bytes += sent_bytes;
        if (received_bytes < BUFFER_SIZE) break;
    }
    return all_sent_bytes;
}

/**
 * @brief Отправляет кэшированные данные клиенту с поддержкой потоковой загрузки
 * @param entry Указатель на запись в кэше, содержащую данные для отправки
 * @param client_socket Дескриптор клиентского сокета для отправки данных
 * @return Общее количество отправленных байт или ERROR при ошибке
 * @details Алгоритм работы:
 *          1. Блокирует мьютекс записи в кэше для безопасного доступа
 *          2. Проходит по цепочке message_t в entry->response
 *          3. Для каждой части сообщения:
 *             а) Отправляет данные клиенту через send_full_data()
 *             б) Обновляет счетчик отправленных байт
 *          4. Если данные еще не полностью загружены в кэш, ожидает на condition variable
 *          5. Просыпается при добавлении новых данных или завершении загрузки
 *          6. Продолжает отправку, пока все данные не будут отправлены
 */
static ssize_t stream_cache_to_client(cache_entry_t *entry, int client_socket) {
    if (entry == NULL) return ERROR;
    ssize_t total_sent = 0; // Общее количество отправленных байт
    pthread_mutex_lock(&entry->mutex); // Блокировка мьютекса
    message_t *curr = entry->response; // Текущая часть сообщения
    message_t *last_sent = NULL; // Последняя отправленная часть
    // Запускает бесконечный цикл отправки данных до тех пор, пока не возникнет ошибка, либо все данные не отправятся, либо удаление записи кэша
    while (1) {
        while (curr != NULL) {
            message_t *to_send = curr; // Сохранение указателя на текущую часть
            pthread_mutex_unlock(&entry->mutex);
            ssize_t sent = send_full_data(client_socket, to_send->part, to_send->part_len); // Отправляет часть сообщения клиенту с гарантией полной отправки.
            if (sent == ERROR) {
                return ERROR;
            }
            total_sent += sent;
            pthread_mutex_lock(&entry->mutex);
            last_sent = to_send; // Запоминает, какую часть только что отправили
            curr = curr->next; // Переход к следующей части
        }
        if (entry->deleted || entry->finished) { // Проверка завершения или удаления записи
            pthread_mutex_unlock(&entry->mutex);
            break;
        }
        pthread_cond_wait(&entry->ready_cond, &entry->mutex); // Блокирует текущий поток в ожидании новых данных
        if (last_sent == NULL) { // еще ничего не отправляли, начинаем с начала
            curr = entry->response;
        } else {
            curr = last_sent->next; //  продолжаем со следующей части после последней отправленной
        }
    }
    return total_sent;
}

/**
 * @brief Извлекает хост и порт из строки URL или адреса сервера
 * @param host_port Входная строка (URL или "host:port")
 * @param host Буфер для сохранения имени хоста
 * @param port Указатель на переменную для сохранения номера порта
 * @return 0 при успехе, ERROR (-1) при ошибке парсинга
 * @details Алгоритм работы:
 *          1. Компилирует регулярное выражение для парсинга URL
 *          2. Выполняет сопоставление регулярного выражения со входной строкой
 *          3. Извлекает хост из соответствующей группы
 *          4. Извлекает порт, если указан, иначе использует порт по умолчанию
 *          5. Определяет порт по умолчанию на основе схемы (http/https)
 *          6. Освобождает ресурсы регулярного выражения
 */
static int get_host_port(const char *host_port, char *host, int *port) {
    regex_t regex = {}; // Регулярное выражение
    char *pattern = "^(http|https)?(://)?([^:/]+)(:([0-9]+))?"; // Паттерн для регулярного выражения
    regmatch_t match[6] = {}; // Массив для хранения результатов сопоставления
    int ret = regcomp(&regex, pattern, REG_EXTENDED); // Компилирует регулярное выражение с указанным паттерном
    if (ret != 0) {
        proxy_log("Host and port getting error: failed to regex pattern compilation");
        return ERROR;
    }
    ret = regexec(&regex, host_port, 6, match, 0); // Выполняет сопоставление регулярного выражения со входной строкой
    if (ret == 0) {
        int host_start = match[3].rm_so; // Извлекает хост из соответствующей группы
        int host_end = match[3].rm_eo;
        strncpy(host, &host_port[host_start], host_end - host_start); // Копирует хост в буфер
        host[host_end - host_start] = '\0';
        int port_start = match[5].rm_so; // Извлекает порт
        int port_end = match[5].rm_eo;
        if (port_start != -1 && port_end != -1) {
            char port_str[port_end - port_start + 1]; // Копирует порт в буфер
            strncpy(port_str, &host_port[port_start], port_end - port_start);
            errno = 0;
            char *end;
            *port = (int) strtol(port_str, &end, 0); // Преобразует строку в целое число
            if (errno != 0) {
                proxy_log("Host and port getting error: %s", strerror(errno));
                return ERROR;
            }
            if (end == port_str) {
                proxy_log("Host and port getting error: no digits were found");
                return ERROR;
            }
        } else {
            *port = (match[1].rm_so != -1 &&
                     match[1].rm_eo != -1 &&
                     strncmp("https", &host_port[match[1].rm_so], match[1].rm_eo - match[1].rm_so) == 0) ? 443 : 80; // Определяет порт по умолчанию
        }
    } else if (ret == REG_NOMATCH) { // Если регулярное выражение не сопоставлено
        proxy_log("Host and port gett   ing error: no host or/and port");
        return ERROR;
    } else {
        char buf[BUFFER_SIZE];
        regerror(ret, &regex, buf, BUFFER_SIZE);
        proxy_log("Host and port getting error: %s", buf);
        return ERROR;
    }
    regfree(&regex);
    return 0;
}

/**
 * @brief Парсит HTTP-запрос и извлекает метод и заголовок Host
 * @param request Строка с HTTP-запросом
 * @param request_len Длина строки запроса
 * @param method Указатель для сохранения указателя на метод в request
 * @param method_len Указатель для сохранения длины метода
 * @param host Указатель для сохранения указателя на значение Host в request
 * @param host_len Указатель для сохранения длины значения Host
 * @return SUCCESS (0) при успехе, ERROR (-1) при ошибке
 * @details Алгоритм работы:
 *          1. Использует библиотеку PicoHTTPParser для парсинга HTTP-запроса
 *          2. Извлекает метод HTTP (GET, POST, CONNECT и т.д.)
 *          3. Ищет заголовок Host в списке заголовков
 *          4. Сохраняет указатели на метод и Host в исходном буфере
 */
static int parse_request(const char *request, size_t request_len, const char **method, size_t *method_len, const char **host, size_t *host_len) {
    char *path; // Указатель на путь
    struct phr_header headers[100]; // Массив заголовков
    size_t path_len, num_headers = 100; // Длина пути и количество заголовков
    int minor_version; // Минорная версия HTTP
    // Разбирает HTTP-запрос и заполняет выходные параметры
    int pret = phr_parse_request(request, request_len, method, method_len, (const char **) &path,
                                 &path_len, &minor_version, headers, &num_headers, 0);
    if (pret == -2) { // Обработка неполного запроса
        proxy_log("Request parsing error: request is partial");
        return ERROR;
    }
    if (pret == -1) { // Если запрос некорректен
        proxy_log("Request parsing error: failed");
        return ERROR;
    }
    for (int i = 0; i < 100; ++i) { // Ищет заголовок Host в массиве заголовков и сохраняет его значение
        if (strncmp(headers[i].name, "Host", 4) == 0) {
            *host = headers[i].value;
            *host_len = headers[i].value_len;
            break;
        }
    }
    if (host == NULL) {
        proxy_log("Request parsing error: host header not found");
        return ERROR;
    }
    return SUCCESS;
}

/**
 * @brief Парсит HTTP-ответ и извлекает статус, длину контента и позицию заголовка Content-Length
 * @param response Строка с HTTP-ответом
 * @param response_len Длина строки ответа
 * @param status Указатель для сохранения HTTP статус-кода (200, 404, 500 и т.д.)
 * @param content_len Указатель для сохранения фактической длины тела ответа
 * @param content_length_header Указатель для сохранения значения заголовка Content-Length
 * @return SUCCESS (0) при успехе, ERROR (-1) при ошибке
 * @details Алгоритм работы:
 *          1. Использует PicoHTTPParser для парсинга HTTP-ответа
 *          2. Извлекает HTTP статус-код
 *          3. Ищет заголовок Content-Length и парсит его значение
 *          4. Вычисляет фактическую длину тела ответа
 *          5. Проверяет корректность формата ответа
 */
static int parse_response(const char *response, size_t response_len, int *status, size_t *content_len, size_t *content_length_header) {
    const char *msg = NULL; // Сообщение cтатуса (например, "OK" для 200)
    struct phr_header headers[100]; // Массив заголовков
    size_t msg_len = 0; // Длина сообщения
    size_t num_headers = 100; // Количество заголовков
    int minor_version = 0; // Минорная версия HTTP
    // Парсинг HTTP-ответа
    int pret = phr_parse_response(response, response_len, &minor_version, status, &msg, &msg_len, headers,
                                  &num_headers, 0);
    if (pret == -2) { // Обработка неполного ответа
        proxy_log("Response parsing error: response is partial");
        return ERROR;
    }
    if (pret == -1) { //. Обработка ошибки парсинга
        proxy_log("Response parsing error: failed");
        return ERROR;
    }
    int content_length_idx = -1;
    // Поиск заголовка Content-Length
    for (int i = 0; i < 100; ++i) {
        if (strncmp(headers[i].name, "Content-Length", 14) == 0) {
            content_length_idx = i;
            break;
        }
    }
    if (content_length_idx == -1) {
        proxy_log("Response parsing error: Content-Length header not found");
        return ERROR;
    }
    errno = 0;
    // Создание временной строки для Content-Length
    char content_length_value[headers[content_length_idx].value_len + 1];
    // Копирует значение Content-Length во временный буфер
    strncpy(content_length_value, headers[content_length_idx].value, headers[content_length_idx].value_len);
    char *end = NULL;
    long temp = strtol(content_length_value, &end, 0); // Преобразует строку Content-Length в число
    *content_length_header = (int) strtol(content_length_value, &end, 0);
    if (errno != 0) {
        proxy_log("Response parsing error: %s", strerror(errno));
        return ERROR;
    }
    if (end == content_length_value) {
        proxy_log("Response parsing error: no digits were found");
        return ERROR;
    }
    *content_length_header = (size_t)temp; // Сохранение значения Content-Length
    // Ищет последовательность "\r\n\r\n", разделяющую заголовки и тело
    char *before_content = strstr(response, "\r\n\r\n");
    if (before_content == NULL) {
        proxy_log("Response parsing error: no newlines before content");
        return ERROR;
    }
    *content_len = response_len - (before_content + 4 - response); // Вычисление фактической длины тела
    return SUCCESS;
}

/**
 * @brief Проверяет, является ли HTTP-запрос кэшируемым
 * @param method Указатель на строку с HTTP-методом
 * @param method_len Длина строки метода
 * @return 1 (true) если метод кэшируемый, 0 (false) если нет
 * @details В текущей реализации кэшируются только GET-запросы.
 */
static int check_request(const char *method, size_t method_len) {
    return strncmp(method, "GET", method_len) == 0; // Сравнивает строку метода с константой "GET"
}

/**
 * @brief Проверяет, является ли HTTP-ответ кэшируемым на основе статус-кода
 * @param status HTTP статус-код ответа (200, 404, 500 и т.д.)
 * @return 1 (true) если ответ можно кэшировать, 0 (false) если нет
 * @details В текущей реализации кэшируются все ответы со статусом < 400.
 * @note Кэшируются успешные ответы (2xx) и перенаправления (3xx)
 * @note Не кэшируются клиентские (4xx) и серверные (5xx) ошибки
 */
static int check_response(int status) {
    return status < 400;
}

/**
 * @brief Находит запись в кэше и ожидает её готовности если необходимо
 * @param cache Указатель на структуру кэша
 * @param request Строка HTTP-запроса для поиска
 * @param request_len Длина строки запроса
 * @return Указатель на найденную запись кэша или NULL если не найдено/удалено
 * @details Алгоритм работы:
 *          1. Ищет запись в кэше по запросу с помощью cache_get()
 *          2. Если запись найдена, но ответ еще не готов (entry->response == NULL):
 *             а) Блокирует мьютекс записи
 *             б) Ожидает на condition variable, пока данные не появятся или запись не удалят
 *             в) Проверяет, не была ли запись удалена во время ожидания
 *             г) Разблокирует мьютекс
 *          3. Возвращает найденную запись или NULL
 * @note Реализует паттерн "ожидание готовности данных" для конкурентного доступа
 * @note Позволяет нескольким клиентам ждать одну и ту же загружаемую запись
 * @note Обрабатывает случай удаления записи во время ожидания
 * @note Гарантирует потокобезопасный доступ к записи кэша
 */
static cache_entry_t *find_cache_entry(cache_t *cache, const char *request, size_t request_len) {
    cache_entry_t *entry = cache_get(cache, request, request_len); // Ищет запись кэша, соответствующую данному HTTP-запросу
    if (entry == NULL) return NULL;
    if (entry->response == NULL) { // Проверяет, готовы ли данные в найденной записи
        // entry->response != NULL: данные готовы (cache hit) → можно сразу использовать
        // entry->response == NULL: данные еще загружаются → нужно подождать
        pthread_mutex_lock(&entry->mutex);
        while (entry->response == NULL && !entry->deleted) pthread_cond_wait(&entry->ready_cond, &entry->mutex); // Ждет, пока данные не появятся или запись не будет удалена
        if (entry->deleted) {
            pthread_mutex_unlock(&entry->mutex);
            return NULL;
        }
        pthread_mutex_unlock(&entry->mutex);
    }
    return entry;
}

#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>

void *mythread(void *arg) {
    printf("mythread tid = %ld\n", pthread_self());
    return NULL;
}

int main() {
    pthread_t tid;
    int err;

    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), gettid());

    while (1) {
        err = pthread_create(&tid, NULL, mythread, NULL);
        if (err) {
            printf("main: pthread_create() failed: %s\n", strerror(err));
            return -1;
        }
    }
    return 0;
}

// main: pthread_create() failed: Resource temporarily unavailable
// pthread_create вызывает системный вызов clone для создания нового потока. Каждый поток получает:
// Уникальный TID
// Собственный стек (~8 МБ по умолчанию, выделяемый через mmap).
// Ресурсы: дескрипторы файлов, обработчики сигналов
// Проблема: Потоки создаются как joinable (по умолчанию), что означает:
// Они не освобождают ресурсы автоматически после завершения (return NULL в mythread).
// Основной поток не вызывает pthread_join, поэтому потоки становятся "зомби" (затратными на ресурсы).
// Результат: Ресурсы (TID, память для стеков, дескрипторы) накапливаются. После создания ~100–1000 потоков (зависит от системы) лимиты исчерпываются, и pthread_create возвращает ошибку.

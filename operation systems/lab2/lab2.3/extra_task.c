#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <string.h>

void test_mutex_type(int type, const char* name) {
    printf("\n=== Testing %s ===\n", name);
    pthread_mutex_t mutex;
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);
    pthread_mutexattr_settype(&attr, type);
    pthread_mutex_init(&mutex, &attr);
    printf("Main: locking mutex...\n");
    pthread_mutex_lock(&mutex);
    void* thread_func(void* arg) {
        printf("Thread 2: trying to unlock mutex...\n");
        int result = pthread_mutex_unlock((pthread_mutex_t*)arg);
        if (result == 0) {
            printf("Thread 2: SUCCESS (THIS IS BAD!)\n");
        } else {
            printf("Thread 2: FAIL! Error: %d (%s)\n", result, strerror(result));
        }
        return NULL;
    }
    pthread_t thread;
    pthread_create(&thread, NULL, thread_func, &mutex);
    pthread_join(thread, NULL);
    pthread_mutex_destroy(&mutex);
    pthread_mutexattr_destroy(&attr);
}

int main() {
    test_mutex_type(PTHREAD_MUTEX_NORMAL, "NORMAL (DEFAULT)");
    test_mutex_type(PTHREAD_MUTEX_ERRORCHECK, "ERRORCHECK");
    test_mutex_type(PTHREAD_MUTEX_RECURSIVE, "RECURSIVE");
    return 0;
}

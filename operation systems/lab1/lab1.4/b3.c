#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

void* thread_func(void* arg) {
    pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
    long counter = 0;
    while (1) {
        counter++;
    }
    return NULL;
}

int main() {
    pthread_t thread;
    if (pthread_create(&thread, NULL, thread_func, NULL) != 0) {
        perror("pthread_create");
        exit(1);
    }

    sleep(3);
    printf("Attempting cancel...\n");
    if (pthread_cancel(thread) != 0) { // ошибок нет, tid валидный
        perror("pthread_cancel");
    }

    void* retval;
    if (pthread_join(thread, &retval) != 0) {
        perror("pthread_join");
    }
    printf("Thread cancelled, retval: %p\n", retval);
    return 0;
}

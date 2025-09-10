#define _GNU_SOURCE
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/syscall.h>

int global_var = 0; // global var (data)

void *mythread(void *arg) {
    int local_var = 123; // local var (stack)
    static int static_var = 456; // local static var (data)
    const int const_var = 789; // local const var (stack)

    printf("mythread [%d %d %ld]: Hello from mythread!\n", getpid(), getppid(), gettid());
    pthread_t tid = pthread_self();
    if (pthread_equal(*(pthread_t *)arg, tid)) {
        printf("pthread_self() thread ID matches pthread_create() thread ID\n");
    } else {
        printf("pthread_self() thread ID does not match pthread_create() thread ID\n");
    }
    
    // pthread_create всегда совпадают, так как pthread_create записывает TID нового потока в tid[i], а pthread_self() возвращает TID текущего потока
    
    // pthread_t — непрозрачный тип, который может быть не числом, а структурой. прямое сравнение pthread_self() == tid неправильно, так как структура pthread_t зависит от реализации. pthread_equal выполянет правильное сравнение, возвращая 1 при совпадении и 0 при несовпадении

    printf("Address of local_var: %p\n", &local_var);
    printf("Address of static_var: %p\n", &static_var);
    printf("Address of const_var: %p\n", &const_var);
    printf("Address of global_var: %p\n", &global_var);

    sleep(30);
    return NULL;
}

int main() {
    pthread_t tid[5];
    int err;
    int i;

    printf("main [%d %d %ld]: Hello from main!\n", getpid(), getppid(), gettid());

    for (i = 0; i < 5; i++) {
        err = pthread_create(&tid[i], NULL, mythread, (void *)&tid[i]);
        if (err) {
            printf("main: pthread_create() failed for thread %d: %s\n", i, strerror(err));
            return -1;
        }
    }

    printf("SLEEPING %d\n", getpid());
    sleep(30);

    for (i = 0; i < 5; i++) {
        err = pthread_join(tid[i], NULL);
        if (err) {
            printf("main: pthread_join() failed for thread %d: %s\n", i, strerror(err));
            return -1;
        }
    }
    return 0;
}

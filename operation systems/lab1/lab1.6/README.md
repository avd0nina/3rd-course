1. Разработать собственную функцию для создания ядерных потоков — аналог `pthread_create()`:
```C
int mythread_create(mythread_t thread, void *(start_routine), void *arg);
```
Функция должна возвращать успех-неуспех.

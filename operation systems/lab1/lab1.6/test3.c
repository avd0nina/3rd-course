#include "mythread.h"
#include <stdio.h>

int main() {
    mythread_t thread;
    void *retval;
    printf("Test3: Trying to create thread with NULL routine...\n");
    if (mythread_create(&thread, NULL, NULL) == 0) {
        printf("Test3: Create succeeded but should fail\n");
        mythread_join(thread, &retval); // Не должно дойти
        return 1;
    }
    printf("Test3: Create failed as expected\n");
    printf("Test3: Passed\n");
    return 0;
}

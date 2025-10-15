#include "uthread.h"
#include <stdio.h>

int main() {
    uthread_t thread;
    void *retval;
    printf("Test3: Initializing library...\n");
    if (uthread_init() == -1) {
        printf("Test3: Initialization failed\n");
        return 1;
    }
    printf("Test3: Trying to create thread with NULL routine...\n");
    if (uthread_create(&thread, NULL, NULL) == 0) {
        printf("Test3: Create succeeded but should fail\n");
        uthread_join(thread, &retval);
        return 1;
    }
    printf("Test3: Create failed as expected\n");
    printf("Test3: Passed\n");
    uthread_cleanup();
    return 0;
}

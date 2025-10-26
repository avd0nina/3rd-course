#define _GNU_SOURCE
#include <pthread.h>
#include <assert.h>
#include <semaphore.h>
#include "queue-sem.h"

void *qmonitor(void *arg) {
    queue_t *q = (queue_t *)arg;
    printf("qmonitor: [%d %d %d]\n", getpid(), getppid(), gettid());
    while (1) {
        queue_print_stats(q);
        sleep(1);
    }
    return NULL;
}

queue_t* queue_init(int max_count) {
    int err;
    queue_t *q = malloc(sizeof(queue_t));
    if (!q) {
        printf("Cannot allocate memory for a queue\n");
        abort();
    }
    
    q->first = NULL;
    q->last = NULL;
    q->max_count = max_count;
    q->count = 0;
    q->shutdown = 0;
    
    err = sem_init(&q->empty_slots, 0, max_count);
    if (err) {
        printf("queue_init: sem_init(empty_slots) failed: %s\n", strerror(err));
        abort();
    }
    
    err = sem_init(&q->filled_slots, 0, 0);
    if (err) {
        printf("queue_init: sem_init(filled_slots) failed: %s\n", strerror(err));
        abort();
    }
    
    err = sem_init(&q->mutex, 0, 1);
    if (err) {
        printf("queue_init: sem_init(mutex) failed: %s\n", strerror(err));
        abort();
    }
    
    q->add_attempts = q->get_attempts = 0;
    q->add_count = q->get_count = 0;
    
    err = pthread_create(&q->qmonitor_tid, NULL, qmonitor, q);
    if (err) {
        printf("queue_init: pthread_create() failed: %s\n", strerror(err));
        abort();
    }
    
    return q;
}

void queue_shutdown(queue_t *q) {
    if (q == NULL) return;
    
    q->shutdown = 1;
    
    for (int i = 0; i < q->max_count; i++) {
        sem_post(&q->empty_slots);
        sem_post(&q->filled_slots);
    }
    sem_post(&q->mutex);
}

void queue_destroy(queue_t *q) {
    if (q == NULL) {
        return;
    }
    
    queue_shutdown(q);
    
    pthread_cancel(q->qmonitor_tid);
    pthread_join(q->qmonitor_tid, NULL);
    
    sem_wait(&q->mutex);
    
    qnode_t *current = q->first;
    while (current != NULL) {
        qnode_t *next = current->next;
        free(current);
        current = next;
    }
    
    sem_post(&q->mutex);
    
    sem_destroy(&q->empty_slots);
    sem_destroy(&q->filled_slots);
    sem_destroy(&q->mutex);
    
    q->first = NULL;
    q->last = NULL;
    q->count = 0;
    free(q);
}

int queue_add(queue_t *q, int val) {
    q->add_attempts++;

    if (sem_wait(&q->empty_slots) != 0) {
        if (q->shutdown) return 0;
        printf("queue_add: sem_wait(empty_slots) failed: %s\n", strerror(errno));
        return 0;
    }
    
    if (q->shutdown) {
        sem_post(&q->empty_slots);
        return 0;
    }

    if (sem_wait(&q->mutex) != 0) {
        sem_post(&q->empty_slots);
        if (q->shutdown) return 0;
        printf("queue_add: sem_wait(mutex) failed: %s\n", strerror(errno));
        return 0;
    }
    
    if (q->shutdown) {
        sem_post(&q->mutex);
        sem_post(&q->empty_slots);
        return 0;
    }
    
    assert(q->count <= q->max_count);

    qnode_t *new = malloc(sizeof(qnode_t));
    if (!new) {
        printf("Cannot allocate memory for new node\n");
        sem_post(&q->mutex);
        sem_post(&q->empty_slots);
        abort();
    }
    
    new->val = val;
    new->next = NULL;

    if (!q->first)
        q->first = q->last = new;
    else {
        q->last->next = new;
        q->last = q->last->next;
    }
    
    q->count++;
    q->add_count++;

    sem_post(&q->mutex);
    sem_post(&q->filled_slots);
    
    return 1;
}

int queue_get(queue_t *q, int *val) {
    q->get_attempts++;

    if (sem_wait(&q->filled_slots) != 0) {
        if (q->shutdown) return 0;
        printf("queue_get: sem_wait(filled_slots) failed: %s\n", strerror(errno));
        return 0;
    }
    
    if (q->shutdown) {
        sem_post(&q->filled_slots);
        return 0;
    }

    if (sem_wait(&q->mutex) != 0) {
        sem_post(&q->filled_slots);
        if (q->shutdown) return 0;
        printf("queue_get: sem_wait(mutex) failed: %s\n", strerror(errno));
        return 0;
    }
    
    if (q->shutdown && q->count == 0) {
        sem_post(&q->mutex);
        sem_post(&q->filled_slots);
        return 0;
    }
    
    assert(q->count >= 0);

    qnode_t *tmp = q->first;
    *val = tmp->val;
    q->first = q->first->next;
    
    free(tmp);
    q->count--;
    q->get_count++;

    sem_post(&q->mutex);
    sem_post(&q->empty_slots);
    
    return 1;
}

void queue_print_stats(queue_t *q) {
    sem_wait(&q->mutex);
    printf("queue stats: current size %d; attempts: (%ld %ld %ld); counts (%ld %ld %ld)\n",
        q->count,
        q->add_attempts, q->get_attempts, q->add_attempts - q->get_attempts,
        q->add_count, q->get_count, q->add_count - q->get_count);
    sem_post(&q->mutex);
}

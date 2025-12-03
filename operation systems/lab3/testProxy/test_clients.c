#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define SERVER_PORT 8081
#define PROXY_PORT 8080
#define TEST_FILE_CONTENT "Hello world!"

// Счётчик обращений к реальному серверу
int request_count = 0;

// HTTP-сервер
void *test_http_server(void *arg) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(SERVER_PORT);
    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 5);
    while (request_count < 2) {
        int client = accept(server_fd, NULL, NULL);
        if (client < 0) continue;
        request_count++;
        char response[1024];
        snprintf(response, sizeof(response),
                 "HTTP/1.1 200 OK\r\nContent-Length: %ld\r\n\r\n%s",
                 strlen(TEST_FILE_CONTENT), TEST_FILE_CONTENT);
        send(client, response, strlen(response), 0);
        close(client);
    }
    close(server_fd);
    return NULL;
}

// Имитация клиента через прокси
void *proxy_client(void *arg) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in proxy_addr = {0};
    proxy_addr.sin_family = AF_INET;
    proxy_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    proxy_addr.sin_port = htons(PROXY_PORT);
    connect(sock, (struct sockaddr *)&proxy_addr, sizeof(proxy_addr));
    char request[512];
    snprintf(request, sizeof(request),
             "GET http://127.0.0.1:%d/file.txt HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n\r\n",
             SERVER_PORT, SERVER_PORT);
    send(sock, request, strlen(request), 0);
    char buffer[1024] = {0};
    recv(sock, buffer, sizeof(buffer)-1, 0);
    printf("Client received: %s\n", buffer);
    close(sock);
    return NULL;
}

int main() {
    pthread_t server_thread, client1, client2;
    pthread_create(&server_thread, NULL, test_http_server, NULL);
    sleep(1); // ждём сервер
    pthread_create(&client1, NULL, proxy_client, NULL);
    usleep(100*1000);
    pthread_create(&client2, NULL, proxy_client, NULL);
    pthread_join(client1, NULL);
    pthread_join(client2, NULL);
    pthread_join(server_thread, NULL);
    printf("Server request count: %d\n", request_count);
    if (request_count == 1) {
        printf("Test passed: second client got response from cache\n");
    } else {
        printf("Test failed: second client triggered new request\n");
    }
    return 0;
}


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <time.h>

#define SERVER_PORT 8081
#define PROXY_PORT 8080
#define TEST_FILE_CONTENT "Hello parallel world!"
#define CLIENT_COUNT 5

// HTTP сервер с задержкой
void *test_http_server(void *arg) {
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
struct sockaddr_in addr = {0};
addr.sin_family = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;
addr.sin_port = htons(SERVER_PORT);
bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
listen(server_fd, 5);
int handled = 0;
while (handled < CLIENT_COUNT) {
    int client = accept(server_fd, NULL, NULL);
    if (client < 0) continue;
    handled++;
    printf("[Server] Handling client %d\n", handled);
    fflush(stdout);
    sleep(2); // искусственная задержка
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

// Клиент через прокси
void *proxy_client(void *arg) {
int id = *(int*)arg;
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
struct timespec ts;
clock_gettime(CLOCK_REALTIME, &ts);
printf("[%ld.%03ld] Client %d received: %.20s...\n",
       ts.tv_sec, ts.tv_nsec/1000000, id, buffer);
close(sock);
return NULL;
}

int main() {
pthread_t server_thread;
pthread_create(&server_thread, NULL, test_http_server, NULL);
sleep(1); // ждём запуск сервера
pthread_t clients[CLIENT_COUNT];
int ids[CLIENT_COUNT];
for (int i = 0; i < CLIENT_COUNT; i++) {
    ids[i] = i+1;
    pthread_create(&clients[i], NULL, proxy_client, &ids[i]);
    usleep(50*1000); // небольшая задержка для перекрытия потоков
}
for (int i = 0; i < CLIENT_COUNT; i++)
    pthread_join(clients[i], NULL);
pthread_join(server_thread, NULL);
printf("All clients finished\n");
return 0;
}

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "env.h"
#include "log.h"
#include "proxy.h"

static void print_usage(char *prog_name);
static int get_port(char *port_str);

int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }
    int handler_count = env_get_client_handler_count();
    time_t cache_expired_time_ms = env_get_cache_expired_time_ms();
    int port = get_port(argv[1]);
    proxy_t *proxy = proxy_create(handler_count, cache_expired_time_ms);
    proxy_log("Proxy PID: %d", getpid());
    proxy_start(proxy, port);
    proxy_destroy(proxy);
    return EXIT_SUCCESS;
}

static void print_usage(char *prog_name) {
    printf("Usage: %s <port>\n", prog_name);
}

static int get_port(char *port_str) {
    errno = 0;
    char *end;
    int handler_count = (int) strtol(port_str, &end, 0);
    if (errno != 0) proxy_log("Port getting error: %s", strerror(errno));
    if (end == port_str) proxy_log("Port getting error: no digits were found");
    return handler_count;
}

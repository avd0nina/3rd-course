cmake_minimum_required(VERSION 3.10)
project(CACHE_PROXY C)

set(CMAKE_C_STANDARD 17)

set(SOURCES
        src/main.c
        src/cache.c
        src/entry.c
        src/env.c
        src/log.c
        src/message.c
        src/proxy.c
        src/thread_pool.c
        picohttpparser/picohttpparser.c
)

set(HEADERS
        include/cache.h
        include/env.h
        include/log.h
        include/message.h
        include/proxy.h
        include/thread_pool.h
        picohttpparser/picohttpparser.h
        include/cache.h
)

add_executable(CACHE_PROXY ${SOURCES} ${HEADERS})

target_include_directories(CACHE_PROXY PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/picohttpparser
)

find_package(Threads REQUIRED)
target_link_libraries(CACHE_PROXY Threads::Threads)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(CACHE_PROXY PRIVATE -Wall -Wextra -Werror)
endif()

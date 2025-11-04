CC      = gcc
CFLAGS  = -Wall -Wextra -Werror -fsanitize=address -fsanitize=leak -pthread -g
LDFLAGS = -fsanitize=address -fsanitize=leak -pthread
TARGET  = mutex_program
SOURCES = main.c queue.c mutex.c
OBJECTS = $(SOURCES:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	ASAN_OPTIONS=detect_leaks=1 ./$(TARGET)

clean:
	rm -f $(TARGET) $(OBJECTS)

.PHONY: all run clean

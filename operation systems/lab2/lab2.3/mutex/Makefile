CC = gcc
CFLAGS = -Wall -Wextra -Werror -fsanitize=address -fsanitize=leak -pthread -g
LDFLAGS = -fsanitize=address -fsanitize=leak

TARGET = mutex
SOURCES = ../queue.c main.c
OBJECTS = $(SOURCES:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET) $(CAP)

clean:
	rm -f $(TARGET) *.o

.PHONY: all run clean

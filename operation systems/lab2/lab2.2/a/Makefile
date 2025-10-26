TARGET = queue-threads
SRCS = queue.c queue-threads.c

CC = gcc
RM = rm
CFLAGS = -g -Wall
LIBS = -lpthread
INCLUDE_DIR = .

all: $(TARGET)

$(TARGET): $(SRCS) queue.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(SRCS) $(LIBS) -o $(TARGET)

clean:
	$(RM) -f *.o $(TARGET)

.PHONY: all clean

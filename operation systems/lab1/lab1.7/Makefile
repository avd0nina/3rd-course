CC = gcc
CFLAGS = -Wall -g -D_GNU_SOURCE
LDFLAGS = -pthread

all: libuthread.a test1 test2 test3 test4 test5

libuthread.a: uthread.o
	ar rcs $@ $^

uthread.o: uthread.c uthread.h
	$(CC) $(CFLAGS) -c uthread.c

test1: test1.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test1.o $(LDFLAGS) -luthread

test1.o: test1.c uthread.h
	$(CC) $(CFLAGS) -c test1.c

test2: test2.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test2.o $(LDFLAGS) -luthread

test2.o: test2.c uthread.h
	$(CC) $(CFLAGS) -c test2.c

test3: test3.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test3.o $(LDFLAGS) -luthread

test3.o: test3.c uthread.h
	$(CC) $(CFLAGS) -c test3.c

test4: test4.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test4.o $(LDFLAGS) -luthread

test4.o: test4.c uthread.h
	$(CC) $(CFLAGS) -c test4.c

test5: test5.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test5.o $(LDFLAGS) -luthread

test5.o: test5.c uthread.h
	$(CC) $(CFLAGS) -c test5.c

clean:
	rm -f *.o *.a test1 test2 test3 test4 test5 stack-*

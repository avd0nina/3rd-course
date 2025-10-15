CC = gcc
CFLAGS = -Wall -g -D_GNU_SOURCE
LDFLAGS = -pthread

all: libuthread.a test1 test2 test3 test4 test5

libuthread.a: uthread.o
	ar rcs $@ $^

uthread.o: uthread.c uthread.h
	$(CC) $(CFLAGS) $(LDFLAGS) -c $<

test1: test1.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test1.o -L. -luthread $(LDFLAGS)

test1.o: test1.c uthread.h
	$(CC) $(CFLAGS) -c $<

test2: test2.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test2.o -L. -luthread $(LDFLAGS)

test2.o: test2.c uthread.h
	$(CC) $(CFLAGS) -c $<

test3: test3.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test3.o -L. -luthread $(LDFLAGS)

test3.o: test3.c uthread.h
	$(CC) $(CFLAGS) -c $<

test4: test4.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test4.o -L. -luthread $(LDFLAGS)

test4.o: test4.c uthread.h
	$(CC) $(CFLAGS) -c $<

test5: test5.o libuthread.a
	$(CC) $(CFLAGS) -o $@ test5.o -L. -luthread $(LDFLAGS)

test5.o: test5.c uthread.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f *.o *.a test1 test2 test3 test4 test5 stack-*

.PHONY: all clean

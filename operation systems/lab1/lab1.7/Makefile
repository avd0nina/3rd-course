CC = gcc
CFLAGS = -Wall -Wextra -Werror -g -D_GNU_SOURCE -fPIC -fsanitize=address -fsanitize=leak -I.
LDFLAGS = -L. -Wl,-rpath,.
SHFLAGS = -shared

all: libuthread.so test1 test2 test3 test4 test5

libuthread.so: uthread.o
	$(CC) $(SHFLAGS) -o $@ $^

uthread.o: uthread.c uthread.h
	$(CC) $(CFLAGS) -c uthread.c

test1: tests/test1.o libuthread.so
	$(CC) $(CFLAGS) -o $@ tests/test1.o $(LDFLAGS) -luthread

test1.o: tests/test1.c uthread.h
	$(CC) $(CFLAGS) -c tests/test1.c -o tests/test1.o

test2: tests/test2.o libuthread.so
	$(CC) $(CFLAGS) -o $@ tests/test2.o $(LDFLAGS) -luthread

test2.o: tests/test2.c uthread.h
	$(CC) $(CFLAGS) -c tests/test2.c -o tests/test2.o

test3: tests/test3.o uthread.so
	$(CC) $(CFLAGS) -o $@ tests/test3.o $(LDFLAGS) -luthread

test3.o: tests/test3.c uthread.h
	$(CC) $(CFLAGS) -c tests/test3.c -o tests/test3.o

test4: tests/test4.o umythread.so
	$(CC) $(CFLAGS) -o $@ tests/test4.o $(LDFLAGS) -luthread

test4.o: tests/test4.c uthread.h
	$(CC) $(CFLAGS) -c tests/test4.c -o tests/test4.o

test5: tests/test5.o umythread.so
	$(CC) $(CFLAGS) -o $@ tests/test5.o $(LDFLAGS) -luthread

test5.o: tests/test5.c uthread.h
	$(CC) $(CFLAGS) -c tests/test5.c -o tests/test5.o

clean:
	rm -f *.o *.so *.a tests/*.o test1 test2 test3 test4 test5 stack-* test2.c.save test2.c.save.*

run: all
	./test1 && ./test2 && ./test2.1 && ./test2.2 && ./test3 && ./test4 && ./test5

CC = gcc
CFLAGS = -Wall -Wextra -Werror -g -D_GNU_SOURCE -fPIC -fsanitize=address -fsanitize=leak -I.
LDFLAGS = -L. -Wl,-rpath,.
SHFLAGS = -shared

all: libmythread.so test1 test2 test3 test4 test5

libmythread.so: mythread.o
	$(CC) $(SHFLAGS) -o $@ $^

mythread.o: mythread.c mythread.h
	$(CC) $(CFLAGS) -c mythread.c

test1: tests/test1.o libmythread.so
	$(CC) $(CFLAGS) -o $@ tests/test1.o $(LDFLAGS) -lmythread

test1.o: tests/test1.c mythread.h
	$(CC) $(CFLAGS) -c tests/test1.c -o tests/test1.o

test2: tests/test2.o libmythread.so
	$(CC) $(CFLAGS) -o $@ tests/test2.o $(LDFLAGS) -lmythread

test2.o: tests/test2.c mythread.h
	$(CC) $(CFLAGS) -c tests/test2.c -o tests/test2.o

test3: tests/test3.o libmythread.so
	$(CC) $(CFLAGS) -o $@ tests/test3.o $(LDFLAGS) -lmythread

test3.o: tests/test3.c mythread.h
	$(CC) $(CFLAGS) -c tests/test3.c -o tests/test3.o

test4: tests/test4.o libmythread.so
	$(CC) $(CFLAGS) -o $@ tests/test4.o $(LDFLAGS) -lmythread

test4.o: tests/test4.c mythread.h
	$(CC) $(CFLAGS) -c tests/test4.c -o tests/test4.o

test5: tests/test5.o libmythread.so
	$(CC) $(CFLAGS) -o $@ tests/test5.o $(LDFLAGS) -lmythread

test5.o: tests/test5.c mythread.h
	$(CC) $(CFLAGS) -c tests/test5.c -o tests/test5.o

clean:
	rm -f *.o *.so *.a tests/*.o test1 test2 test3 test4 test5 stack-* test2.c.save test2.c.save.*

run: all
	./test1 && ./test2 && ./test2.1 && ./test2.2 && ./test3 && ./test4 && ./test5

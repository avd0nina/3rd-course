CC = gcc
CFLAGS = -Wall -Wextra -Werror -g -D_GNU_SOURCE -fPIC -fsanitize=address -fsanitize=leak
LDFLAGS = -L. -Wl,-rpath,.

all: libmythread.so test1 test2 test3 test4 test5

libmythread.so: mythread.o
	$(CC) -shared -o $@ $^ $(CFLAGS)

mythread.o: mythread.c mythread.h
	$(CC) $(CFLAGS) -c mythread.c

test1: test1.o libmythread.so
	$(CC) $(CFLAGS) -o $@ test1.o $(LDFLAGS) -lmythread

test1.o: test1.c mythread.h
	$(CC) $(CFLAGS) -c test1.c

test2: test2.o libmythread.so
	$(CC) $(CFLAGS) -o $@ test2.o $(LDFLAGS) -lmythread

test2.o: test2.c mythread.h
	$(CC) $(CFLAGS) -c test2.c

test3: test3.o libmythread.so
	$(CC) $(CFLAGS) -o $@ test3.o $(LDFLAGS) -lmythread

test3.o: test3.c mythread.h
	$(CC) $(CFLAGS) -c test3.c

test4: test4.o libmythread.so
	$(CC) $(CFLAGS) -o $@ test4.o $(LDFLAGS) -lmythread

test4.o: test4.c mythread.h
	$(CC) $(CFLAGS) -c test4.c

test5: test5.o libmythread.so
	$(CC) $(CFLAGS) -o $@ test5.o $(LDFLAGS) -lmythread

test5.o: test5.c mythread.h
	$(CC) $(CFLAGS) -c test5.c

clean:
	rm -f *.o *.so test1 test2 test3 test4 test5 stack-*

run: all
	./test1 && ./test2 && ./test3 && ./test4 && ./test5

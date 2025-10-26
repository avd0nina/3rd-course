TARGET_1 = queue-threads-size-usleep
SRCS_1 = queue.c queue-threads-size-usleep.c

TARGET_2 = queue-threads-cpu-usleep
SRCS_2 = queue.c queue-threads-cpu-usleep.c

TARGET_3 = queue-threads-noyield-usleep
SRCS_3 = queue.c queue-threads-noyield-usleep.c

CC=gcc
RM=rm
CFLAGS= -g -Wall
LIBS=-lpthread
INCLUDE_DIR="."

all: ${TARGET_1} ${TARGET_2} ${TARGET_3}

${TARGET_1}: queue.h ${SRCS_1}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_1} ${LIBS} -o ${TARGET_1}

${TARGET_2}: queue.h ${SRCS_2}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_2} ${LIBS} -o ${TARGET_2}

${TARGET_3}: queue.h ${SRCS_3}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_3} ${LIBS} -o ${TARGET_3}

clean:
	${RM} -f *.o ${TARGET_1} ${TARGET_2} ${TARGET_3} 

.PHONY: all clean

TARGET_1 = queue-threads-size
SRCS_1 = queue.c queue-threads-size.c

TARGET_2 = queue-threads-size-usleep
SRCS_2 = queue.c queue-threads-size-usleep.c

TARGET_3 = queue-threads-cpu
SRCS_3 = queue.c queue-threads-cpu.c

TARGET_4 = queue-threads-cpu-usleep
SRCS_4 = queue.c queue-threads-cpu-usleep.c

TARGET_5 = queue-threads-noyield
SRCS_5 = queue.c queue-threads-noyield.c

TARGET_6 = queue-threads-noyield-usleep
SRCS_6 = queue.c queue-threads-noyield-usleep.c

CC=gcc
RM=rm
CFLAGS= -g -Wall
LIBS=-lpthread
INCLUDE_DIR="."

all: ${TARGET_1} ${TARGET_2} ${TARGET_3} ${TARGET_4} ${TARGET_5} ${TARGET_6}

${TARGET_1}: queue.h ${SRCS_1}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_1} ${LIBS} -o ${TARGET_1}

${TARGET_2}: queue.h ${SRCS_2}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_2} ${LIBS} -o ${TARGET_2}

${TARGET_3}: queue.h ${SRCS_3}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_3} ${LIBS} -o ${TARGET_3}

${TARGET_4}: queue.h ${SRCS_4}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_3} ${LIBS} -o ${TARGET_3}
  
${TARGET_5}: queue.h ${SRCS_5}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_3} ${LIBS} -o ${TARGET_3}

${TARGET_6}: queue.h ${SRCS_6}
	${CC} ${CFLAGS} -I${INCLUDE_DIR} ${SRCS_3} ${LIBS} -o ${TARGET_3}

clean:
	${RM} -f *.o ${TARGET_1} ${TARGET_2} ${TARGET_3} ${TARGET_4} ${TARGET_5} ${TARGET_6}

.PHONY: all clean

# Компилятор
CC = gcc

# Флаги компиляции
CFLAGS = -Wall -g -pthread

# Список поддиректорий
LAB_DIRS = lab1.1 lab1.2 lab1.3 lab1.4 lab1.5 lab1.6 lab1.7

# Найдем все C файлы и создадим соответствующие исполняемые файлы
C_SOURCES = $(wildcard lab1.*/*.c)
EXECUTABLES = $(C_SOURCES:.c=)

# Цель по умолчанию: компилировать все программы
all: $(EXECUTABLES)

# Правило компиляции
%: %.c
	$(CC) $(CFLAGS) $< -o $@

# Цель для запуска всех программ
run: all
	@for exec in $(EXECUTABLES); do \
		if [ -f "$$exec" ]; then \
			echo "Running $$exec..."; \
			./$$exec; \
			echo "----------------"; \
		else \
			echo "Executable $$exec not found!"; \
		fi; \
	done

# Цель для запуска программ в конкретной поддиректории
run-lab1.%: all
	@for exec in lab1.$*/*; do \
		if [ -f "$$exec" ] && [ -x "$$exec" ] && [ "$${exec##*.}" != "c" ]; then \
			echo "Running $$exec..."; \
			./$$exec; \
			echo "----------------"; \
		fi; \
	done

# Цель для запуска одной конкретной программы
run-%: %
	@if [ -f "$<" ]; then \
		echo "Running $<..."; \
		./$<; \
	else \
		echo "Executable $< not found!"; \
	fi

# Цель для очистки
clean:
	rm -f $(EXECUTABLES)
	@for dir in $(LAB_DIRS); do \
		rm -f $$dir/*.o $$dir/stack-* $$dir/*~; \
	done

.PHONY: all run clean

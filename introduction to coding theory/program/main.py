import itertools
import time
from collections import defaultdict

def hamming_weight(x): # Вес Хэмминга числа (0..127)
    return bin(x).count('1')

def hamming_distance(x, y): # Расстояние Хэмминга между двумя целыми числами
    return hamming_weight(x ^ y) # XOR. Единицы в различающихся позициях

def bit_permute(x, perm): # Перестановка координат числа x
    res = 0
    for i in range(7):
        if (x >> i) & 1:
          res |= (1 << perm[i])
    return res

# Пример:
# x = 0b1011001
# perm = (0,2,4,6,1,3,5)
# res = 0b1100011
def get_canonical_rep(codewords): # Каноническая форма кода
    # Перебираем все перестановки координат (7! = 5040), применяем каждую ко всем словам кода,
    # сортируем список чисел и сравниваем кортежи лексикографически. Выбираем наименьший кортеж.
    min_code = None
    for perm in itertools.permutations(range(7)): # перебираем перестановки СТОЛБЦОВ
        transformed = [bit_permute(w, perm) for w in codewords]
        transformed.sort() # переставляем СТРОКИ в канонический порядок
        tup = tuple(transformed)
        if min_code is None or tup < min_code:
            min_code = tup
    return min_code

def build_hamming_code(): # Строим стандартный [7,4,3] код Хэмминга
    code = []
    for x in range(128): # Перебираем всевозможные двоичные 7-битные векторы (2^7 = 128)
        syndrome = 0
        for i in range(7):
            if (x >> i) & 1:
                syndrome ^= (i + 1)
        if syndrome == 0:
            code.append(x)
    code.sort()
    return code # в итоге здесь 16 кодовых слов
# Пример
# x = 7 = 0b0000111
# i = 0: бит = 1 → syndrome = 0 ^ 1 = 1
# i = 1: бит = 1 → syndrome = 1 ^ 2 = 3
# i = 2: бит = 1 → syndrome = 3 ^ 3 = 0 => x - кодовое слово

def main():
    start_time = time.time()
    hamming_code = build_hamming_code()
    hamming_canon = get_canonical_rep(hamming_code)

    # Шар радиуса 1 вокруг 0 покрывает: 0 и все векторы веса 1
    # Это 8 векторов: 0, и 7 векторов веса 1
    ball_zero_set = {0} | {1 << i for i in range(7)}
    
    # Остальные 120 векторов нужно покрыть 15 непересекающимися шарами
    # Каждый шар содержит центр и 7 соседей на расстоянии 1

    # Центр должен иметь вес >= 3 (чтобы расстояние до 0 было >= 3)
    ball_masks = {}
    candidates = []
    for c in range(1, 128):
        if hamming_weight(c) < 3:
            continue
        # Строим шар радиуса 1 вокруг c
        ball = [c]
        for i in range(7):
            ball.append(c ^ (1 << i))
        # Шар не должен пересекаться с шаром вокруг 0
        if any(v in ball_zero_set for v in ball):
            continue
        mask = sum(1 << v for v in ball) # битовая маска, единица на позиции v означает, что вектор v принадлежит этому шару.
        ball_masks[c] = mask
        candidates.append(c)

    # Векторы, которые нужно покрыть (все кроме шара вокруг 0)
    to_cover = 0
    for x in range(128):
        if x not in ball_zero_set:
            to_cover |= (1 << x)

    # Для каждого вектора pos, который еще не покрыт — список центров, которые его покрывают
    covers = defaultdict(list)
    for c in candidates:
        mask = ball_masks[c]
        bit = mask
        while bit:
            pos = (bit & -bit).bit_length() - 1 # находим позицию младшего установленного бита в bit
            if (to_cover & (1 << pos)): # проверяет, установлен ли бит pos в to_cover. если да,то вектор ещё не покрыт
                covers[pos].append(c)
            bit &= bit - 1

    solutions = []

    def search(remaining, selected): # remaining - векторы, которые нужно покрыть, selected - центры шаров, которые уже выбраны в качестве кодовых слов
        if remaining == 0: # все векторы покрыты
            if len(selected) == 15:
                solutions.append(sorted(selected))
            return
        # Выбираем позицию с минимальным числом вариантов (эвристика)
        min_count = float('inf')
        best_pos = -1
        bit = remaining
        while bit:
            pos = (bit & -bit).bit_length() - 1
            # перебираем все центры, которые могут покрыть вектор pos
            # для каждого центра проверяем условие
            # условие истинно, если шар не пересекается с уже покрытыми векторами => генератор выдает 1
            # складываем все эти единицы, получая количество центров, удовлетворяющих условию
            count = sum(1 for c in covers[pos] if (ball_masks[c] & ~remaining) == 0)
            if count == 0:
                return
            if count < min_count:
                min_count = count
                best_pos = pos
            bit &= bit - 1
        if best_pos == -1:
            return
        for c in covers[best_pos]:
            ball = ball_masks[c]
            if (ball & ~remaining) != 0: # проверяем пересечение
                continue
            new_remaining = remaining & ~ball # новая битовая маска c векторами, которые останутся непокрытыми после добавления центра c.
            selected.append(c)
            search(new_remaining, selected)
            selected.pop()

    search(to_cover, [])
    print(f"Найдено наборов центров: {len(solutions)}")
    # Обработка найденных решений
    unique_canonical = set()
    hamming_equivalent_count = 0
    for i, centers in enumerate(solutions, 1):
        code = [0] + centers
        code.sort()
        # Проверка минимального расстояния d ≥ 3
        min_d = 7
        for j in range(len(code)):
            for k in range(j + 1, len(code)):
                dist = hamming_distance(code[j], code[k])
                if dist < min_d:
                    min_d = dist
        if min_d < 3:
            print(f"  Решение {i}: d = {min_d} → отброшено")
            continue
        canon = get_canonical_rep(code)
        unique_canonical.add(canon)
        if canon == hamming_canon:
            hamming_equivalent_count += 1
            print(f"  Решение {i}: 16 слов, d = {min_d}, ЭКВИВАЛЕНТЕН коду Хэмминга")
        else:
            print(f"  Решение {i}: 16 слов, d = {min_d}, ДРУГОЙ класс!")

    print(f"Уникальных канонических форм: {len(unique_canonical)}")
    print(f"Эквивалентны коду Хэмминга: {hamming_equivalent_count}")

    if len(unique_canonical) == 1:
        print("\nВЫВОД:")
        print("Существует ровно ОДИН класс эквивалентности.")
        print("Все совершенные двоичные коды длины 7 с кодовым расстоянием 3")
        print("эквивалентны коду Хэмминга [7,4,3].")
        print("(Нелинейных совершенных кодов с этими параметрами не существует.)")
    else:
        print("\nОбнаружены разные классы эквивалентности!")

    total_ms = int((time.time() - start_time) * 1000)
    print(f"\nTime: {total_ms}ms")

if __name__ == "__main__":
    main()
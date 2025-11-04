import numpy as np

def tridiagonal_solve(A, B, C, F):
    """
    Решение системы с трехдиагональной матрицей методом прогонки
    A - элементы под главной диагональю (размер n-1)
    B - элементы на главной диагонали (размер n)
    C - элементы над главной диагональю (размер n-1)
    F - правая часть системы уравнений (размер n)
    """
    n = len(B)

    if n == 1:
        return np.array([F[0] / B[0]])

    # Прямой ход
    alpha = np.zeros(n - 1)
    beta = np.zeros(n)
    alpha[0] = C[0] / B[0]
    beta[0] = F[0] / B[0]
    for i in range(1, n - 1):
        denominator = B[i] - A[i - 1] * alpha[i - 1]
        alpha[i] = C[i] / denominator
        beta[i] = (F[i] - A[i - 1] * beta[i - 1]) / denominator

    beta[n - 1] = (F[n - 1] - A[n - 2] * beta[n - 2]) / (B[n - 1] - A[n - 2] * alpha[n - 2])

    # Обратный ход
    x = np.zeros(n)
    x[n - 1] = beta[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = beta[i] - alpha[i] * x[i + 1]
    return x

def test_system_1(n):
    """Тест 1: A - трехдиагональная матрица с 2 на диагонали и -1 на побочных, f = [2, 2, ..., 2]"""
    A = np.zeros(n - 1)  # нижняя диагональ
    B = np.zeros(n)  # главная диагональ
    C = np.zeros(n - 1)  # верхняя диагональ
    F = np.zeros(n)  # правая часть
    for i in range(n):
        B[i] = 2.0
        if i < n - 1:
            A[i] = -1.0
            C[i] = -1.0
        F[i] = 2.0
    return A, B, C, F

def test_system_2(n, epsilon):
    """Тест 2: A - трехдиагональная матрица с 2 на диагонали и -1 на побочных, f = [2+ε, 2+ε, ..., 2+ε]"""
    A = np.zeros(n - 1)  # нижняя диагональ
    B = np.zeros(n)  # главная диагональ
    C = np.zeros(n - 1)  # верхняя диагональ
    F = np.zeros(n)  # правая часть
    for i in range(n):
        B[i] = 2.0
        if i < n - 1:
            A[i] = -1.0
            C[i] = -1.0
        F[i] = 2.0 + epsilon
    return A, B, C, F

def test_system_3(n, gamma):
    """Тест 3: ci = 2i + gamma, fi = 2(i+1) + gamma"""
    A = np.zeros(n - 1)  # нижняя диагональ
    B = np.zeros(n)  # главная диагональ
    C = np.zeros(n - 1)  # верхняя диагональ
    F = np.zeros(n)  # правая часть
    for i in range(n):
        B[i] = 2 * (i + 1) + gamma  # ci = 2i + gamma, индексация с 1
        if i < n - 1:
            A[i] = -1.0
            C[i] = -1.0
        F[i] = 2 * (i + 2) + gamma  # fi = 2(i+1) + gamma, индексация с 1
    return A, B, C, F

def print_system(A, B, C, F, n):
    """Вывод системы уравнений"""
    print("\nСистема уравнений:")
    for i in range(n):
        if i == 0:
            print(f"{B[i]:.2f}x{i + 1} + {C[i]:.2f}x{i + 2} = {F[i]:.2f}")
        elif i == n - 1:
            print(f"{A[i - 1]:.2f}x{i} + {B[i]:.2f}x{i + 1} = {F[i]:.2f}")
        else:
            print(f"{A[i - 1]:.2f}x{i} + {B[i]:.2f}x{i + 1} + {C[i]:.2f}x{i + 2} = {F[i]:.2f}")

def main():
    print("Решение СЛАУ с трехдиагональной матрицей методом прогонки")
    print("=" * 60)
    # Ввод параметров
    while True:
        try:
            n = int(input("Введите размерность матрицы n (n >= 2): "))
            if n >= 2:
                break
            else:
                print("Размерность должна быть не меньше 2!")
        except ValueError:
            print("Пожалуйста, введите целое число!")
    while True:
        try:
            epsilon = float(input("Введите значение ε: "))
            break
        except ValueError:
            print("Пожалуйста, введите число!")
    while True:
        try:
            gamma = float(input("Введите значение γ: "))
            break
        except ValueError:
            print("Пожалуйста, введите число!")
    print(f"\nПараметры: n = {n}, ε = {epsilon}, γ = {gamma}")

    # Тест 1
    print("\n" + "=" * 50)
    print("ТЕСТ 1")
    print("=" * 50)
    A1, B1, C1, F1 = test_system_1(n)
    print_system(A1, B1, C1, F1, n)
    x1 = tridiagonal_solve(A1, B1, C1, F1)
    print(f"\nРешение x = {x1}")

    # Проверка решения
    residual = np.zeros(n)
    for i in range(n):
        if i == 0:
            residual[i] = B1[i] * x1[i] + C1[i] * x1[i + 1] - F1[i]
        elif i == n - 1:
            residual[i] = A1[i - 1] * x1[i - 1] + B1[i] * x1[i] - F1[i]
        else:
            residual[i] = A1[i - 1] * x1[i - 1] + B1[i] * x1[i] + C1[i] * x1[i + 1] - F1[i]
    print(f"Невязка: {residual}")
    print(f"Максимальная невязка: {np.max(np.abs(residual)):.2e}")

    # Тест 2
    print("\n" + "=" * 50)
    print("ТЕСТ 2")
    print("=" * 50)
    A2, B2, C2, F2 = test_system_2(n, epsilon)
    print_system(A2, B2, C2, F2, n)
    x2 = tridiagonal_solve(A2, B2, C2, F2)
    print(f"\nРешение x = {x2}")

    # Проверка решения
    residual2 = np.zeros(n)
    for i in range(n):
        if i == 0:
            residual2[i] = B2[i] * x2[i] + C2[i] * x2[i + 1] - F2[i]
        elif i == n - 1:
            residual2[i] = A2[i - 1] * x2[i - 1] + B2[i] * x2[i] - F2[i]
        else:
            residual2[i] = A2[i - 1] * x2[i - 1] + B2[i] * x2[i] + C2[i] * x2[i + 1] - F2[i]

    print(f"Невязка: {residual2}")
    print(f"Максимальная невязка: {np.max(np.abs(residual2)):.2e}")

    # Тест 3
    print("\n" + "=" * 50)
    print("ТЕСТ 3")
    print("=" * 50)
    A3, B3, C3, F3 = test_system_3(n, gamma)
    print_system(A3, B3, C3, F3, n)
    x3 = tridiagonal_solve(A3, B3, C3, F3)
    print(f"\nРешение x = {x3}")

    # Проверка решения
    residual3 = np.zeros(n)
    for i in range(n):
        if i == 0:
            residual3[i] = B3[i] * x3[i] + C3[i] * x3[i + 1] - F3[i]
        elif i == n - 1:
            residual3[i] = A3[i - 1] * x3[i - 1] + B3[i] * x3[i] - F3[i]
        else:
            residual3[i] = A3[i - 1] * x3[i - 1] + B3[i] * x3[i] + C3[i] * x3[i + 1] - F3[i]

    print(f"Невязка: {residual3}")
    print(f"Максимальная невязка: {np.max(np.abs(residual3)):.2e}")

if __name__ == "__main__":
    main()

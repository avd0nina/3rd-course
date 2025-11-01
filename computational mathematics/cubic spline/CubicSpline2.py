import numpy as np
import matplotlib.pyplot as plt

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
        beta[i] = (F[i] + A[i - 1] * beta[i - 1]) / denominator
    beta[n - 1] = (F[n - 1] + A[n - 2] * beta[n - 2]) / (B[n - 1] - A[n - 2] * alpha[n - 2])

    # Обратный ход
    x = np.zeros(n)
    x[n - 1] = beta[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = alpha[i] * x[i + 1] + beta[i]
    return x

def build_cubic_spline(x, y, boundary_condition='natural', beta0=None, beta_n=None):
    """
    Построение кубического сплайна
    x, y - узлы интерполяции
    boundary_condition: 'natural' (γ_0=γ_n=0) или 'clamped' (заданы производные)
    beta0, beta_n - значения производных на концах (для clamped)
    """
    n = len(x) - 1  # количество интервалов
    h = np.diff(x)  # шаги сетки, x_{i+1} - x_i
    delta_y = np.diff(y)  # вычисление правых частей для системы, y_{i+1} - y_i

    if boundary_condition == 'natural':
        # Естественный сплайн: γ_0 = γ_n = 0
        # Система для γ_1,...,γ_{n-1}
        if n - 1 <= 0:  # если только 2 точки
            gamma = np.zeros(n + 1)

            def spline_function(x_val):
                for i in range(n):
                    if x[i] <= x_val <= x[i + 1]:
                        return y[i] + (y[i + 1] - y[i]) * (x_val - x[i]) / h[
                            i]  # линейная функция, прмямая линия между точками (x_0, y_0) и (x_1, y_1)
                return None

            return spline_function, gamma
        A = np.zeros(n - 1)  # нижняя диагональ
        B = np.zeros(n - 1)  # главная диагональ
        C = np.zeros(n - 1)  # верхняя диагональ
        F = np.zeros(n - 1)  # правая часть
        for i in range(n - 1):
            A[i] = h[i] / 6
            B[i] = (h[i] + h[i + 1]) / 3
            C[i] = h[i + 1] / 6
            F[i] = (delta_y[i + 1] / h[i + 1]) - (delta_y[i] / h[i])
        # Решаем систему для γ_1,...,γ_{n-1}
        gamma_inner = tridiagonal_solve(A, B, C, F)
        # Собираем полный вектор γ
        gamma = np.zeros(n + 1)
        gamma[0] = 0  # γ0 = 0
        gamma[n] = 0  # γn = 0
        gamma[1:n] = gamma_inner

    elif boundary_condition == 'clamped':
        # Сплайн с заданными производными на концах
        # Система для γ_0,...,γ_n
        A = np.zeros(n)  # нижняя диагональ
        B = np.zeros(n + 1)  # главная диагональ
        C = np.zeros(n)  # верхняя диагональ
        F = np.zeros(n + 1)  # правая часть
        # Первое уравнение
        B[0] = h[0] / 3
        C[0] = h[0] / 6
        F[0] = (y[1] - y[0]) / h[0] - beta0
        # Внутренние уравнения
        for i in range(1, n):
            A[i - 1] = h[i - 1] / 6
            B[i] = (h[i - 1] + h[i]) / 3
            C[i] = h[i] / 6
            F[i] = (y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1]
        # Последнее уравнение
        A[n - 1] = h[n - 1] / 6
        B[n] = h[n - 1] / 3
        F[n] = beta_n - (y[n] - y[n - 1]) / h[n - 1]
        # Решаем систему для γ_0,...,γ_n
        gamma = tridiagonal_solve(A, B, C, F)

    # Теперь строим сплайн на каждом интервале
    def spline_function(x_val):
        # Находим интервал, в который попадает x_val
        if x_val < x[0] or x_val > x[-1]:
            return None
        for i in range(n):
            if x[i] <= x_val <= x[i + 1]:
                # Формула (2.69) из теории
                term1 = y[i] * (x[i + 1] - x_val) / h[i]
                term2 = y[i + 1] * (x_val - x[i]) / h[i]
                term3 = gamma[i] * ((x[i + 1] - x_val) ** 3 - h[i] ** 2 * (x[i + 1] - x_val)) / (6 * h[i])
                term4 = gamma[i + 1] * ((x_val - x[i]) ** 3 - h[i] ** 2 * (x_val - x[i])) / (6 * h[i])
                return term1 + term2 + term3 + term4
        return None
    return spline_function, gamma

def f(x):
    """Исходная функция f(x) = |x|"""
    return np.abs(x)

def main():
    # Ввод числа узлов
    while True:
        try:
            n = int(input("Введите число узлов интерполяции n (n >= 2): "))
            if n >= 2:
                break
            else:
                print("Число узлов должно быть не меньше 2!")
        except ValueError:
            print("Пожалуйста, введите целое число!")

    # Создание равномерной сетки на отрезке [-1, 1]
    x_nodes = np.linspace(-1, 1, n)
    y_nodes = f(x_nodes)

    print(f"\nУзлы интерполяции (n = {n}):")
    for i in range(n):
        print(f"x_{i} = {x_nodes[i]:.3f}, f(x_{i}) = {y_nodes[i]:.3f}")

    # Построение сплайна
    spline_func, gamma = build_cubic_spline(x_nodes, y_nodes, boundary_condition='natural')

    # Создание точек для графиков
    x_plot = np.linspace(-1, 1, 1000)
    y_original = f(x_plot)
    y_spline = np.array([spline_func(x) for x in x_plot])

    # Построение графиков
    plt.figure(figsize=(12, 8))

    # График исходной функции
    plt.plot(x_plot, y_original, 'b-', linewidth=2, label='f(x) = |x|')

    # График сплайна
    plt.plot(x_plot, y_spline, 'r--', linewidth=2, label='Кубический сплайн')

    # Узлы интерполяции
    plt.plot(x_nodes, y_nodes, 'ko', markersize=6, label='Узлы интерполяции')

    # Настройки графика
    plt.xlabel('x', fontsize=12)
    plt.ylabel('f(x)', fontsize=12)
    plt.title(f'Интерполяция функции f(x) = |x| кубическим сплайном (n = {n} узлов)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)

    # Добавляем информацию о коэффициентах
    plt.text(0.02, 0.98, f'Число узлов: {n}\nКоэффициенты γ: {np.round(gamma, 4)}',
             transform=plt.gca().transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

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
    delta_y = np.diff(y) # вычисление правых частей для системы, y_{i+1} - y_i

    if boundary_condition == 'natural':
        # Естественный сплайн: γ_0 = γ_n = 0
        # Система для γ_1,...,γ_{n-1}
        if n - 1 <= 0:  # если только 2 точки
            gamma = np.zeros(n + 1)
            def spline_function(x_val):
                for i in range(n):
                    if x[i] <= x_val <= x[i + 1]:
                        return y[i] + (y[i + 1] - y[i]) * (x_val - x[i]) / h[i] # линейная функция, прмямая линия между точками (x_0, y_0) и (x_1, y_1)
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

# Данные из задания
x_i = np.array([-1, 0, 2, 3, 5])
f_i = np.array([1, 2, 4, 1, -3])

# Построение сплайна
spline_func, gamma = build_cubic_spline(x_i, f_i, boundary_condition='natural')

# Создание точек для построения графика
x_plot = np.linspace(x_i[0], x_i[-1], 1000) # создает 1000 равномерно распределенных точек от -1 до 5
y_plot = np.array([spline_func(x) for x in x_plot])

# Построение графика
plt.figure(figsize=(12, 8))

# График сплайна
plt.plot(x_plot, y_plot, 'b-', linewidth=2, label='Кубический сплайн')

# Исходные точки
plt.plot(x_i, f_i, 'ro', markersize=8, label='Исходные точки')

# Настройки графика
plt.xlabel('x', fontsize=12)
plt.ylabel('f(x)', fontsize=12)
plt.title('Интерполяционный кубический сплайн', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)

# Добавляем информацию о коэффициентах γ
plt.text(0.02, 0.98, f'Коэффициенты γ: {np.round(gamma, 4)}',
         transform=plt.gca().transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Вывод дополнительной информации
print("Узлы интерполяции:")
for i in range(len(x_i)):
    print(f"x_{i} = {x_i[i]}, f_{i} = {f_i[i]}")

print(f"\nКоэффициенты γ: {gamma}")
print(f"\nЗначения сплайна в узлах:")
for i in range(len(x_i)):
    spline_val = spline_func(x_i[i])
    print(f"S({x_i[i]}) = {spline_val:.6f} (должно быть {f_i[i]})")

plt.show()
